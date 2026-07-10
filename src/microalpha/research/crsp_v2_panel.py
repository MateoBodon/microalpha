"""DuckDB adapter for the manifest-bound CRSP CIZ/DSF-v2 monthly panel."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .crsp_v2 import (
    CRSPV2Error,
    audit_source_protocol,
    load_protocol,
    protocol_sha256,
    sha256_file,
)


def _duckdb() -> Any:
    try:
        import duckdb
    except ImportError as exc:  # pragma: no cover - environment-specific
        raise CRSPV2Error(
            "DuckDB is required; install microalpha[research] before building "
            "the CRSP-v2 panel"
        ) from exc
    return duckdb


def _sql_literal(value: str | Path) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def _sql_list(values: list[str]) -> str:
    return "[" + ", ".join(_sql_literal(value) for value in values) + "]"


def _ff12_case(column: str = "siccd") -> str:
    groups: list[tuple[str, str]] = [
        (
            "NoDur",
            f"({column} BETWEEN 100 AND 999 OR {column} BETWEEN 2000 AND 2399 "
            f"OR {column} BETWEEN 2700 AND 2749 OR {column} BETWEEN 2770 AND 2799 "
            f"OR {column} BETWEEN 3100 AND 3199 OR {column} BETWEEN 3940 AND 3989)",
        ),
        (
            "Durbl",
            f"({column} BETWEEN 2500 AND 2519 OR {column} BETWEEN 2590 AND 2599 "
            f"OR {column} BETWEEN 3630 AND 3659 OR {column} BETWEEN 3710 AND 3711 "
            f"OR {column} = 3714 OR {column} = 3716 "
            f"OR {column} BETWEEN 3750 AND 3751 OR {column} = 3792 "
            f"OR {column} BETWEEN 3900 AND 3939 OR {column} BETWEEN 3990 AND 3999)",
        ),
        (
            "Manuf",
            f"({column} BETWEEN 2520 AND 2589 OR {column} BETWEEN 2600 AND 2699 "
            f"OR {column} BETWEEN 2750 AND 2769 OR {column} BETWEEN 3000 AND 3099 "
            f"OR {column} BETWEEN 3200 AND 3569 OR {column} BETWEEN 3580 AND 3629 "
            f"OR {column} BETWEEN 3700 AND 3709 OR {column} BETWEEN 3712 AND 3713 "
            f"OR {column} = 3715 OR {column} BETWEEN 3717 AND 3749 "
            f"OR {column} BETWEEN 3752 AND 3791 OR {column} BETWEEN 3793 AND 3799 "
            f"OR {column} BETWEEN 3830 AND 3839 OR {column} BETWEEN 3860 AND 3899)",
        ),
        (
            "Enrgy",
            f"({column} BETWEEN 1200 AND 1399 OR {column} BETWEEN 2900 AND 2999)",
        ),
        (
            "Chems",
            f"({column} BETWEEN 2800 AND 2829 OR {column} BETWEEN 2840 AND 2899)",
        ),
        (
            "BusEq",
            f"({column} BETWEEN 3570 AND 3579 OR {column} BETWEEN 3660 AND 3692 "
            f"OR {column} BETWEEN 3694 AND 3699 OR {column} BETWEEN 3810 AND 3829 "
            f"OR {column} BETWEEN 7370 AND 7379)",
        ),
        ("Telcm", f"({column} BETWEEN 4800 AND 4899)"),
        ("Utils", f"({column} BETWEEN 4900 AND 4949)"),
        (
            "Shops",
            f"({column} BETWEEN 5000 AND 5999 OR {column} BETWEEN 7200 AND 7299 "
            f"OR {column} BETWEEN 7600 AND 7699)",
        ),
        (
            "Hlth",
            f"({column} BETWEEN 2830 AND 2839 OR {column} = 3693 "
            f"OR {column} BETWEEN 3840 AND 3859 OR {column} BETWEEN 8000 AND 8099)",
        ),
        ("Money", f"({column} BETWEEN 6000 AND 6999)"),
    ]
    clauses = " ".join(
        f"WHEN {condition} THEN {_sql_literal(label)}" for label, condition in groups
    )
    return f"CASE {clauses} ELSE 'Other' END"


def _split_case(protocol: Mapping[str, Any], column: str = "formation_date") -> str:
    windows = protocol["windows"]
    clauses: list[str] = []
    for name in ("warmup", "training", "validation", "final_holdout"):
        window = windows[name]
        clauses.append(
            f"WHEN {column} BETWEEN DATE {_sql_literal(window['start'])} "
            f"AND DATE {_sql_literal(window['end'])} THEN {_sql_literal(name)}"
        )
    return "CASE " + " ".join(clauses) + " ELSE 'outside' END"


def _read_frozen_model(
    path: str | Path,
    *,
    protocol: Mapping[str, Any],
    expected_protocol_sha256: str,
) -> dict[str, Any]:
    frozen_path = Path(path).expanduser().resolve()
    if not frozen_path.is_file():
        raise CRSPV2Error(f"Frozen model record not found: {frozen_path}")
    payload = json.loads(frozen_path.read_text(encoding="utf-8"))
    required = {
        "protocol_id": str(protocol["protocol_id"]),
        "protocol_sha256": expected_protocol_sha256,
        "validation_complete": True,
    }
    for key, expected in required.items():
        if payload.get(key) != expected:
            raise CRSPV2Error(f"Frozen model record has invalid {key}")
    candidate = payload.get("selected_candidate")
    if not isinstance(candidate, dict) or not payload.get("frozen_at_utc"):
        raise CRSPV2Error("Frozen model record is incomplete")
    allowed_signals = set(protocol["candidate_grid"]["signals"])
    allowed_weighting = set(protocol["candidate_grid"]["weighting"])
    if candidate.get("signal") not in allowed_signals:
        raise CRSPV2Error("Frozen model record selected an unknown signal")
    if candidate.get("weighting") not in allowed_weighting:
        raise CRSPV2Error("Frozen model record selected an unknown weighting")
    return payload


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:  # pragma: no cover - non-Git execution
        return "unknown"


def _require_new_artifact_paths(output_path: Path, manifest_path: Path) -> None:
    """Fail closed before work if either final artifact name is already occupied."""

    occupied = [
        str(path)
        for path in (output_path, manifest_path)
        if os.path.lexists(path)
    ]
    if occupied:
        raise CRSPV2Error(
            "Refusing to overwrite existing panel artifacts: " + ", ".join(occupied)
        )


def _publish_artifact_pair_no_clobber(
    staged_output: Path,
    output_path: Path,
    staged_manifest: Path,
    manifest_path: Path,
) -> None:
    """Publish two same-filesystem artifacts without replacing either target."""

    published: list[tuple[Path, Path]] = []
    try:
        for source, destination in (
            (staged_output, output_path),
            (staged_manifest, manifest_path),
        ):
            os.link(source, destination)
            published.append((source, destination))
    except OSError as exc:
        for source, destination in reversed(published):
            try:
                if destination.exists() and os.path.samefile(source, destination):
                    destination.unlink()
            except OSError:
                pass
        raise CRSPV2Error(
            "Panel artifact pair could not be published without clobbering"
        ) from exc


def build_monthly_panel(
    protocol_path: str | Path,
    output_path: str | Path,
    *,
    stage: str = "selection",
    frozen_model_path: str | Path | None = None,
    memory_limit: str = "4GB",
    temp_directory: str | Path | None = None,
) -> dict[str, Any]:
    """Build a derived monthly panel without exposing raw licensed rows.

    ``stage='selection'`` never opens final-holdout daily partitions and only
    materializes side-table rows that match opened daily rows through the
    validation cutoff. The CIZ daily row is the authoritative point-in-time
    source; ``stocknames_v2`` is used only to audit date coverage and overlapping
    history. The side tables are gzip CSVs, so their unpartitioned source bytes
    are necessarily scanned to apply that filter; the receipt says so explicitly.
    ``stage='final'`` requires a protocol-bound frozen model receipt before any
    final-holdout daily partition is opened.
    """

    if stage not in {"selection", "final"}:
        raise CRSPV2Error("stage must be selection or final")
    protocol_path = Path(protocol_path).expanduser().resolve()
    protocol = load_protocol(protocol_path)
    protocol_digest = protocol_sha256(protocol_path)
    output_path = Path(output_path).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path = output_path.with_suffix(output_path.suffix + ".manifest.json")
    _require_new_artifact_paths(output_path, manifest_path)
    frozen_model: dict[str, Any] | None = None
    if stage == "final":
        if frozen_model_path is None:
            raise CRSPV2Error("Final panel requires a frozen model record")
        frozen_model = _read_frozen_model(
            frozen_model_path,
            protocol=protocol,
            expected_protocol_sha256=protocol_digest,
        )
    audit = audit_source_protocol(protocol_path)

    selection_start = str(protocol["windows"]["warmup"]["start"])
    validation_end = str(protocol["windows"]["validation"]["end"])
    validation_end_year = int(validation_end[:4])
    materialization_end = (
        validation_end
        if stage == "selection"
        else str(protocol["windows"]["final_holdout"]["end"])
    )
    source_paths = list(audit["primary"]["paths"])
    if stage == "selection":
        source_paths = [
            path
            for path in source_paths
            if int(Path(path).parent.name.split("=")[1]) <= validation_end_year
        ]
    if not source_paths:
        raise CRSPV2Error("No CRSP-v2 source partitions selected")
    if stage == "selection" and any(
        int(Path(path).parent.name.split("=")[1]) > validation_end_year
        for path in source_paths
    ):
        raise CRSPV2Error("Selection stage attempted to include holdout data")

    primary_spec = protocol["dataset"]["wrds"]["primary_manifest"]
    side_paths = audit["primary"]["side_tables"]
    names_path = side_paths["stocknames_v2"]["path"]
    delists_path = side_paths["stkdelists"]["path"]
    rules = protocol["universe"]["filters_at_formation_date"]

    staging_directory = tempfile.TemporaryDirectory(
        prefix=f".{output_path.name}.staging-", dir=output_path.parent
    )
    staging_root = Path(staging_directory.name)
    staged_output_path = staging_root / output_path.name
    staged_manifest_path = staging_root / manifest_path.name
    staged_daily_path = staging_root / "_daily_filtered.parquet"
    if temp_directory is None:
        temp_directory = output_path.parent / "_duckdb_tmp"
    temp_directory = Path(temp_directory).expanduser().resolve()
    temp_directory.mkdir(parents=True, exist_ok=True)

    duckdb = _duckdb()
    connection = duckdb.connect()
    try:
        connection.execute(f"SET memory_limit={_sql_literal(memory_limit)}")
        connection.execute(f"SET temp_directory={_sql_literal(temp_directory)}")
        connection.execute("SET preserve_insertion_order=false")
        connection.execute("SET threads=2")

        daily_csv = _sql_list(source_paths)
        connection.execute(f"""
            CREATE TEMP VIEW daily_raw AS
            SELECT * FROM read_csv(
                {daily_csv}, header=true, all_varchar=true, union_by_name=true
            )
            """)
        connection.execute(f"""
            CREATE TEMP TABLE daily AS
            SELECT
                try_cast(permno AS BIGINT) AS permno,
                try_cast(permco AS BIGINT) AS permco,
                try_cast(siccd AS INTEGER) AS siccd,
                sharetype,
                securitytype,
                securitysubtype,
                usincflg,
                primaryexch,
                conditionaltype,
                tradingstatusflg,
                try_cast(dlycaldt AS DATE) AS date,
                dlydelflg,
                try_cast(dlyprc AS DOUBLE) AS price,
                try_cast(dlycap AS DOUBLE) * 1000.0 AS market_cap_usd,
                try_cast(dlyret AS DOUBLE) AS total_return,
                dlyretmissflg,
                try_cast(dlyvol AS DOUBLE) AS volume,
                try_cast(dlyprcvol AS DOUBLE) AS dollar_volume_usd,
                try_cast(dlybid AS DOUBLE) AS bid,
                try_cast(dlyask AS DOUBLE) AS ask,
                try_cast(dlyopen AS DOUBLE) AS open,
                ticker
            FROM daily_raw
            WHERE try_cast(permno AS BIGINT) IS NOT NULL
              AND try_cast(dlycaldt AS DATE) IS NOT NULL
              AND try_cast(dlycaldt AS DATE) BETWEEN
                  DATE {_sql_literal(selection_start)}
                  AND DATE {_sql_literal(materialization_end)}
            """)
        duplicate_daily = connection.execute("""
            SELECT count(*) FROM (
                SELECT permno, date
                FROM daily
                GROUP BY permno, date
                HAVING count(*) <> 1
            )
            """).fetchone()[0]
        if duplicate_daily:
            raise CRSPV2Error("CRSP-v2 daily permno/date keys are not unique")

        # The permitted daily slice is much larger than the finished monthly
        # panel. Persist it temporarily, then release the in-memory table before
        # rolling-window work so the caller's memory cap remains meaningful.
        connection.execute(f"""
            COPY daily TO {_sql_literal(staged_daily_path)}
            (FORMAT PARQUET, COMPRESSION ZSTD, ROW_GROUP_SIZE 100000)
            """)
        connection.execute("DROP TABLE daily")
        connection.execute(f"""
            CREATE TEMP VIEW daily AS
            SELECT * FROM read_parquet({_sql_literal(staged_daily_path)})
            """)

        effective_name_end = (
            "least(coalesce(n.nameenddt, DATE '9999-12-31'), "
            f"DATE {_sql_literal(validation_end)})"
            if stage == "selection"
            else "n.nameenddt"
        )
        connection.execute(f"""
            CREATE TEMP TABLE names AS
            WITH parsed AS (
                SELECT
                    try_cast(permno AS BIGINT) AS permno,
                    try_cast(permco AS BIGINT) AS permco,
                    try_cast(namedt AS DATE) AS namedt,
                    try_cast(nameenddt AS DATE) AS nameenddt,
                    ticker,
                    primaryexch,
                    conditionaltype,
                    tradingstatusflg,
                    sharetype,
                    securitytype,
                    securitysubtype,
                    usincflg,
                    try_cast(siccd AS INTEGER) AS siccd
                FROM read_csv(
                    {_sql_literal(names_path)}, header=true, all_varchar=true
                )
            )
            SELECT
                n.permno,
                n.permco,
                n.namedt,
                {effective_name_end} AS nameenddt,
                n.ticker,
                n.primaryexch,
                n.conditionaltype,
                n.tradingstatusflg,
                n.sharetype,
                n.securitytype,
                n.securitysubtype,
                n.usincflg,
                n.siccd
            FROM parsed n
            WHERE n.permno IS NOT NULL
              AND n.namedt IS NOT NULL
              AND n.namedt <= DATE {_sql_literal(materialization_end)}
              AND coalesce(n.nameenddt, DATE '9999-12-31') >=
                  DATE {_sql_literal(selection_start)}
              AND EXISTS (
                  SELECT 1
                  FROM daily d
                  WHERE coalesce(d.dlydelflg, 'N') <> 'Y'
                    AND d.permno = n.permno
                    AND d.date BETWEEN n.namedt
                        AND coalesce(n.nameenddt, DATE '9999-12-31')
              )
            """)
        name_match_summary = connection.execute("""
            SELECT
                count(*) FILTER (WHERE source_matches = 0) AS missing_rows,
                count(*) FILTER (WHERE source_matches > 1) AS ambiguous_rows,
                count(DISTINCT permno) FILTER (
                    WHERE source_matches = 0
                ) AS missing_permnos,
                min(date) FILTER (WHERE source_matches = 0) AS first_missing_date,
                max(date) FILTER (WHERE source_matches = 0) AS last_missing_date,
                max(source_matches) AS maximum_matches
            FROM (
                SELECT d.permno, d.date, count(n.permno) AS source_matches
                FROM daily d
                LEFT JOIN names n
                  ON d.permno = n.permno
                 AND d.date BETWEEN n.namedt
                     AND coalesce(n.nameenddt, DATE '9999-12-31')
                WHERE coalesce(d.dlydelflg, 'N') <> 'Y'
                GROUP BY d.permno, d.date
            ) match_counts
            """).fetchone()
        missing_name_matches = int(name_match_summary[0])
        ambiguous_name_matches = int(name_match_summary[1])
        maximum_name_matches = int(name_match_summary[5])
        if missing_name_matches:
            raise CRSPV2Error(
                "Point-in-time stocknames coverage failed: "
                f"missing_rows={missing_name_matches}, "
                f"affected_permnos={int(name_match_summary[2])}, "
                f"date_range={name_match_summary[3]}..{name_match_summary[4]}"
            )

        connection.execute("""
            CREATE TEMP VIEW daily_resolved AS
            SELECT
                d.permno,
                d.permco,
                d.siccd,
                d.sharetype,
                d.securitytype,
                d.securitysubtype,
                d.usincflg,
                d.primaryexch,
                d.conditionaltype,
                d.tradingstatusflg,
                d.date,
                d.dlydelflg,
                d.price,
                d.market_cap_usd,
                d.total_return,
                d.dlyretmissflg,
                d.volume,
                d.dollar_volume_usd,
                d.bid,
                d.ask,
                d.open,
                d.ticker
            FROM daily d
            """)

        connection.execute(f"""
            CREATE TEMP TABLE delists AS
            WITH parsed AS (
                SELECT
                    try_cast(permno AS BIGINT) AS permno,
                    try_cast(deldlydt AS DATE) AS deldlydt,
                    try_cast(delret AS DOUBLE) AS delret,
                    delretmisstype
                FROM read_csv(
                    {_sql_literal(delists_path)}, header=true, all_varchar=true
                )
            )
            SELECT x.*
            FROM parsed x
            JOIN daily d
              ON d.dlydelflg = 'Y'
             AND d.permno = x.permno
             AND d.date = x.deldlydt
            WHERE x.permno IS NOT NULL
              AND x.deldlydt BETWEEN DATE {_sql_literal(selection_start)}
                  AND DATE {_sql_literal(materialization_end)}
            """)
        duplicate_delists = connection.execute("""
            SELECT count(*) FROM (
                SELECT permno, deldlydt
                FROM delists
                GROUP BY permno, deldlydt
                HAVING count(*) <> 1
            )
            """).fetchone()[0]
        if duplicate_delists:
            raise CRSPV2Error("stkdelists permno/deldlydt keys are not unique")
        delisting_mismatches = connection.execute("""
            SELECT count(*)
            FROM daily d
            LEFT JOIN delists x
              ON d.permno = x.permno AND d.date = x.deldlydt
            WHERE d.dlydelflg = 'Y'
              AND (
                    x.permno IS NULL
                 OR (d.total_return IS NULL) <> (x.delret IS NULL)
                 OR (
                    d.total_return IS NOT NULL AND x.delret IS NOT NULL
                    AND abs(d.total_return - x.delret) > 0.0000005
                 )
                 OR (
                    d.dlyretmissflg IS NOT NULL AND x.delretmisstype IS NOT NULL
                    AND d.dlyretmissflg <> x.delretmisstype
                 )
              )
            """).fetchone()[0]
        if delisting_mismatches:
            raise CRSPV2Error(
                f"CIZ/stkdelists reconciliation failed for {delisting_mismatches} rows"
            )
        access_summary = connection.execute(f"""
            SELECT
                (SELECT count(*) FROM daily) AS daily_rows,
                (SELECT count(*) FROM daily
                    WHERE date > DATE {_sql_literal(validation_end)})
                    AS post_validation_daily_rows,
                (SELECT count(*) FROM names) AS name_rows,
                (SELECT max(namedt) FROM names) AS max_namedt,
                (SELECT max(nameenddt) FROM names) AS max_nameenddt,
                (SELECT count(*) FROM names
                    WHERE namedt > DATE {_sql_literal(validation_end)}
                       OR nameenddt > DATE {_sql_literal(validation_end)})
                    AS post_validation_name_rows,
                (SELECT count(*) FROM delists) AS delist_rows,
                (SELECT max(deldlydt) FROM delists) AS max_deldlydt,
                (SELECT count(*) FROM delists
                    WHERE deldlydt > DATE {_sql_literal(validation_end)})
                    AS post_validation_delist_rows,
                {ambiguous_name_matches} AS overlapping_name_history_daily_rows,
                {maximum_name_matches} AS maximum_date_valid_name_matches
            """).fetchone()

        connection.execute("""
            CREATE TEMP VIEW daily_features AS
            SELECT
                *,
                median(
                    CASE WHEN coalesce(dlydelflg, 'N') <> 'Y'
                         THEN dollar_volume_usd END
                ) OVER (
                    PARTITION BY permno ORDER BY date
                    ROWS BETWEEN 59 PRECEDING AND CURRENT ROW
                ) AS adv_60_usd,
                stddev_samp(total_return) OVER (
                    PARTITION BY permno ORDER BY date
                    ROWS BETWEEN 125 PRECEDING AND CURRENT ROW
                ) AS volatility_126d,
                CASE
                    WHEN bid > 0 AND ask >= bid AND (ask + bid) > 0
                    THEN (ask - bid) / ((ask + bid) / 2.0) * 10000.0
                END AS full_spread_bps
            FROM daily_resolved
            """)
        industry_sql = _ff12_case("siccd")
        split_sql = _split_case(protocol)
        allowed_sharetype = _sql_list([str(x) for x in rules["sharetype"]])
        allowed_securitytype = _sql_list([str(x) for x in rules["securitytype"]])
        allowed_subtype = _sql_list([str(x) for x in rules["securitysubtype"]])
        allowed_usinc = _sql_list([str(x) for x in rules["usincflg"]])
        allowed_exchange = _sql_list([str(x) for x in rules["primaryexch"]])
        allowed_conditional = _sql_list([str(x) for x in rules["conditionaltype"]])
        allowed_status = _sql_list([str(x) for x in rules["tradingstatusflg"]])
        connection.execute(f"""
            CREATE TEMP VIEW monthly_panel AS
            WITH monthly_base AS (
                SELECT
                    permno,
                    last_day(date) AS formation_date,
                    arg_max(permco, date) FILTER (WHERE coalesce(dlydelflg, 'N') <> 'Y') AS permco,
                    arg_max(ticker, date) FILTER (WHERE coalesce(dlydelflg, 'N') <> 'Y') AS ticker,
                    arg_max(siccd, date) FILTER (WHERE coalesce(dlydelflg, 'N') <> 'Y') AS siccd,
                    arg_max(sharetype, date) FILTER (WHERE coalesce(dlydelflg, 'N') <> 'Y') AS sharetype,
                    arg_max(securitytype, date) FILTER (WHERE coalesce(dlydelflg, 'N') <> 'Y') AS securitytype,
                    arg_max(securitysubtype, date) FILTER (WHERE coalesce(dlydelflg, 'N') <> 'Y') AS securitysubtype,
                    arg_max(usincflg, date) FILTER (WHERE coalesce(dlydelflg, 'N') <> 'Y') AS usincflg,
                    arg_max(primaryexch, date) FILTER (WHERE coalesce(dlydelflg, 'N') <> 'Y') AS primaryexch,
                    arg_max(conditionaltype, date) FILTER (WHERE coalesce(dlydelflg, 'N') <> 'Y') AS conditionaltype,
                    arg_max(tradingstatusflg, date) FILTER (WHERE coalesce(dlydelflg, 'N') <> 'Y') AS tradingstatusflg,
                    arg_max(abs(price), date) FILTER (WHERE coalesce(dlydelflg, 'N') <> 'Y') AS price,
                    arg_max(market_cap_usd, date) FILTER (WHERE coalesce(dlydelflg, 'N') <> 'Y') AS market_cap_usd,
                    arg_max(adv_60_usd, date) FILTER (WHERE coalesce(dlydelflg, 'N') <> 'Y') AS adv_60_usd,
                    arg_max(volatility_126d, date) FILTER (WHERE coalesce(dlydelflg, 'N') <> 'Y') AS volatility_126d,
                    arg_max(full_spread_bps, date) FILTER (WHERE coalesce(dlydelflg, 'N') <> 'Y') AS full_spread_bps,
                    CASE
                        WHEN count(total_return) = 0 THEN NULL
                        ELSE product(1.0 + total_return) FILTER (WHERE total_return IS NOT NULL) - 1.0
                    END AS monthly_total_return,
                    count(*) FILTER (WHERE dlydelflg = 'Y') AS delisting_pseudo_days
                FROM daily_features
                GROUP BY permno, last_day(date)
            ),
            monthly AS (
                SELECT
                    *,
                    count(monthly_total_return) OVER (
                        PARTITION BY permno ORDER BY formation_date
                        ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
                    ) AS history_months
                FROM monthly_base
            )
            SELECT
                *,
                {industry_sql} AS industry,
                {split_sql} AS split,
                (
                    sharetype IN {allowed_sharetype}
                    AND securitytype IN {allowed_securitytype}
                    AND securitysubtype IN {allowed_subtype}
                    AND usincflg IN {allowed_usinc}
                    AND primaryexch IN {allowed_exchange}
                    AND conditionaltype IN {allowed_conditional}
                    AND tradingstatusflg IN {allowed_status}
                    AND price >= {float(rules['minimum_price'])}
                    AND market_cap_usd >= {float(rules['minimum_market_cap_usd'])}
                    AND adv_60_usd >= {float(rules['minimum_60d_median_dollar_volume_usd'])}
                    AND history_months >= {int(rules['minimum_return_history_months'])}
                ) AS eligible_at_formation
            FROM monthly
            """)

        connection.execute(f"""
            COPY (
                SELECT * FROM monthly_panel
                WHERE split <> 'outside'
                  {"AND split <> 'final_holdout'" if stage == "selection" else ""}
                ORDER BY formation_date, permno
            ) TO {_sql_literal(staged_output_path)}
            (FORMAT PARQUET, COMPRESSION ZSTD, ROW_GROUP_SIZE 100000)
            """)
        summary_row = connection.execute(f"""
            SELECT
                count(*) AS rows,
                count(DISTINCT permno) AS permnos,
                min(formation_date) AS min_date,
                max(formation_date) AS max_date,
                count(*) FILTER (WHERE eligible_at_formation) AS eligible_rows,
                sum(delisting_pseudo_days) AS delisting_pseudo_days
            FROM read_parquet({_sql_literal(staged_output_path)})
            """).fetchone()
    finally:
        connection.close()

    output_digest = sha256_file(staged_output_path)
    manifest_payload: dict[str, Any] = {
        "schema_version": "microalpha-derived-crsp-v2-panel/v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "stage": stage,
        "protocol_id": str(protocol["protocol_id"]),
        "protocol_path": str(protocol_path),
        "protocol_sha256": protocol_digest,
        "dataset_id": str(protocol["dataset"]["id"]),
        "source_primary_manifest": str(primary_spec["path"]),
        "source_primary_manifest_sha256": str(primary_spec["sha256"]),
        "source_partition_count": len(source_paths),
        "source_partitions": source_paths,
        "holdout_headers_verified": True,
        "access_contract": {
            "primary_holdout_partitions_opened_for_outcome_rows": any(
                int(Path(path).parent.name.split("=")[1]) > validation_end_year
                for path in source_paths
            ),
            "primary_post_validation_rows_materialized": int(access_summary[1]),
            "side_table_source_layout": "unpartitioned_gzip_csv",
            "side_table_source_bytes_scan_scope": "full_files_for_date_key_filter",
            "side_table_materialization_end": materialization_end,
            "post_validation_stocknames_rows_materialized": int(access_summary[5]),
            "post_validation_delisting_rows_materialized": int(access_summary[8]),
            "stage_access_summary": (
                "No final-holdout daily partition is opened beyond permitted header "
                "verification; unpartitioned side-table files are scanned, but only "
                "rows matching opened daily rows through the validation cutoff are "
                "materialized, checked, reconciled, or used."
                if stage == "selection"
                else "The protocol-bound frozen-model receipt was validated before "
                "final-holdout daily outcome rows and matching side-table rows were "
                "materialized."
            ),
        },
        "side_table_materialization": {
            "stocknames_v2": {
                "rows": int(access_summary[2]),
                "max_namedt": (
                    None if access_summary[3] is None else str(access_summary[3])
                ),
                "max_effective_nameenddt": (
                    None if access_summary[4] is None else str(access_summary[4])
                ),
                "daily_rows_without_date_valid_name": missing_name_matches,
                "daily_rows_with_overlapping_name_history": int(access_summary[9]),
                "maximum_date_valid_name_matches": int(access_summary[10]),
                "attribute_resolution": (
                    "CIZ daily row is authoritative; stocknames_v2 is a "
                    "date-coverage and overlap audit only"
                ),
            },
            "stkdelists": {
                "rows": int(access_summary[6]),
                "max_deldlydt": (
                    None if access_summary[7] is None else str(access_summary[7])
                ),
            },
        },
        "frozen_model": frozen_model,
        "git_sha": _git_sha(),
        "output": {
            "path": str(output_path),
            "sha256": output_digest,
            "size_bytes": staged_output_path.stat().st_size,
            "rows": int(summary_row[0]),
            "permnos": int(summary_row[1]),
            "min_date": str(summary_row[2]),
            "max_date": str(summary_row[3]),
            "eligible_rows": int(summary_row[4]),
            "delisting_pseudo_days": int(summary_row[5] or 0),
        },
        "return_semantics": "CIZ dlyret used once; stkdelists is reconciliation-only",
        "build_resources": {
            "duckdb_memory_limit": memory_limit,
            "duckdb_threads": 2,
            "filtered_daily_intermediate": (
                "temporary same-filesystem parquet removed after publication"
            ),
        },
    }
    staged_manifest_path.write_text(
        json.dumps(manifest_payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    manifest_digest = hashlib.sha256(staged_manifest_path.read_bytes()).hexdigest()
    _publish_artifact_pair_no_clobber(
        staged_output_path,
        output_path,
        staged_manifest_path,
        manifest_path,
    )
    manifest_payload["manifest_path"] = str(manifest_path)
    manifest_payload["manifest_sha256"] = manifest_digest
    staging_directory.cleanup()
    return manifest_payload


__all__ = ["build_monthly_panel"]
