#!/usr/bin/env python3
"""Generate machine-derived indices for project_state.

Stdlib only. Writes JSON outputs to project_state/_generated.
"""
from __future__ import annotations

import ast
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
GENERATED_DIR = ROOT / "project_state" / "_generated"


def rg_files(root: Path) -> list[str]:
    try:
        result = subprocess.check_output(["rg", "--files"], cwd=root, text=True)
        files = [line.strip() for line in result.splitlines() if line.strip()]
        return files
    except (subprocess.CalledProcessError, FileNotFoundError):
        files = []
        for dirpath, _, filenames in os.walk(root):
            for name in filenames:
                full = Path(dirpath) / name
                files.append(str(full.relative_to(root)))
        return files


def add_explicit_dirs(files: list[str], root: Path, extra_dirs: list[Path]) -> list[str]:
    seen = set(files)
    for directory in extra_dirs:
        if not directory.exists():
            continue
        for path in directory.rglob("*"):
            if path.is_file():
                rel = str(path.relative_to(root))
                if rel not in seen:
                    files.append(rel)
                    seen.add(rel)
    return files


def classify_role(path: str) -> str:
    if path.startswith("src/"):
        return "source"
    if path.startswith("tests/"):
        return "test"
    if path.startswith("configs/"):
        return "config"
    if path.startswith("docs/"):
        return "doc"
    if path.startswith("notebooks/"):
        return "notebook"
    if path.startswith("reports/"):
        return "report"
    if path.startswith("artifacts/"):
        return "artifact"
    if path.startswith("data/") or path.startswith("data_sp500/") or path.startswith("data_sp500_enriched/"):
        return "data"
    if path.startswith("scripts/"):
        return "script"
    if path.startswith("examples/"):
        return "example"
    if path.startswith("benchmarks/"):
        return "benchmark"
    if path.startswith("metadata/"):
        return "metadata"
    if path.startswith("project_state/"):
        return "project_state"
    if path.startswith("tools/"):
        return "tool"
    return "root" if "/" not in path else "other"


def is_binary_extension(path: str) -> bool:
    ext = Path(path).suffix.lower()
    return ext in {
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".pdf",
        ".zip",
        ".parquet",
        ".feather",
        ".pkl",
        ".pickle",
        ".npy",
        ".npz",
        ".csv",
        ".tsv",
        ".xlsx",
        ".xls",
        ".h5",
        ".hdf5",
        ".sqlite",
        ".db",
    }


def repo_inventory(files: list[str]) -> list[dict[str, Any]]:
    inventory: list[dict[str, Any]] = []
    for path in files:
        full = ROOT / path
        try:
            size = full.stat().st_size
        except FileNotFoundError:
            size = None
        inventory.append(
            {
                "path": path,
                "size_bytes": size,
                "role": classify_role(path),
                "ext": Path(path).suffix.lower(),
                "binary_ext": is_binary_extension(path),
            }
        )
    return inventory


def module_name_for_file(path: Path) -> str:
    rel = path.relative_to(ROOT)
    if rel.parts[0] != "src":
        return ""
    parts = list(rel.parts[1:])
    if not parts:
        return ""
    if parts[-1].endswith(".py"):
        parts[-1] = parts[-1][:-3]
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(["microalpha"] + parts)


def unparse(node: ast.AST | None) -> str:
    if node is None:
        return ""
    try:
        return ast.unparse(node)
    except Exception:
        return ""


def format_args(args: ast.arguments) -> str:
    def fmt_arg(arg: ast.arg) -> str:
        text = arg.arg
        if arg.annotation is not None:
            ann = unparse(arg.annotation)
            if ann:
                text += f": {ann}"
        return text

    posonly = [fmt_arg(a) for a in args.posonlyargs]
    regular = [fmt_arg(a) for a in args.args]
    kwonly = [fmt_arg(a) for a in args.kwonlyargs]

    defaults = [unparse(d) for d in args.defaults]
    if defaults:
        for i, dval in enumerate(defaults):
            idx = len(posonly) + len(regular) - len(defaults) + i
            if idx < 0:
                continue
            if idx < len(posonly):
                posonly[idx] = f"{posonly[idx]}={dval}"
            else:
                j = idx - len(posonly)
                if 0 <= j < len(regular):
                    regular[j] = f"{regular[j]}={dval}"

    if args.vararg is not None:
        vararg = fmt_arg(args.vararg)
        vararg = f"*{vararg}"
    else:
        vararg = ""

    kw_defaults = [unparse(d) if d is not None else "" for d in args.kw_defaults]
    if kwonly:
        for i, dval in enumerate(kw_defaults):
            if dval:
                kwonly[i] = f"{kwonly[i]}={dval}"

    if args.kwarg is not None:
        kwarg = fmt_arg(args.kwarg)
        kwarg = f"**{kwarg}"
    else:
        kwarg = ""

    parts: list[str] = []
    if posonly:
        parts.extend(posonly)
        parts.append("/")
    parts.extend(regular)
    if vararg:
        parts.append(vararg)
    if kwonly:
        if not vararg:
            parts.append("*")
        parts.extend(kwonly)
    if kwarg:
        parts.append(kwarg)
    return f"({', '.join(parts)})"


def first_line(doc: str | None) -> str:
    if not doc:
        return ""
    return doc.strip().splitlines()[0].strip()


def symbol_index(py_files: list[Path]) -> dict[str, Any]:
    index: dict[str, Any] = {}
    for path in py_files:
        rel = str(path.relative_to(ROOT))
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        try:
            tree = ast.parse(text, filename=rel)
        except SyntaxError:
            continue
        module_doc = first_line(ast.get_docstring(tree))
        funcs: list[dict[str, str]] = []
        classes: list[dict[str, str]] = []
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                funcs.append(
                    {
                        "name": node.name,
                        "signature": format_args(node.args),
                        "doc": first_line(ast.get_docstring(node)),
                        "async": isinstance(node, ast.AsyncFunctionDef),
                    }
                )
            elif isinstance(node, ast.ClassDef):
                bases = [unparse(b) for b in node.bases]
                classes.append(
                    {
                        "name": node.name,
                        "bases": [b for b in bases if b],
                        "doc": first_line(ast.get_docstring(node)),
                    }
                )
        index[rel] = {
            "module_doc": module_doc,
            "functions": funcs,
            "classes": classes,
        }
    return index


def import_graph(py_files: list[Path]) -> dict[str, list[str]]:
    module_map: dict[Path, str] = {}
    for path in py_files:
        mod = module_name_for_file(path)
        if mod:
            module_map[path] = mod

    graph: dict[str, list[str]] = {}
    for path in py_files:
        rel = str(path.relative_to(ROOT))
        try:
            text = path.read_text(encoding="utf-8")
            tree = ast.parse(text, filename=rel)
        except Exception:
            continue

        current_module = module_map.get(path, "")
        imports: set[str] = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("microalpha"):
                        imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.level and current_module:
                    parts = current_module.split(".")
                    base_parts = parts[:-node.level]
                    if node.module:
                        base_parts += node.module.split(".")
                    if base_parts:
                        mod = ".".join(base_parts)
                        if mod.startswith("microalpha"):
                            imports.add(mod)
                elif node.module and node.module.startswith("microalpha"):
                    imports.add(node.module)

        graph[rel] = sorted(imports)
    return graph


def make_targets(makefile: Path) -> list[str]:
    if not makefile.exists():
        return []
    text = makefile.read_text(encoding="utf-8")
    targets: set[str] = set()
    for line in text.splitlines():
        if not line or line.startswith("\t"):
            continue
        if line.lstrip().startswith("#"):
            continue
        match = re.match(r"^([A-Za-z0-9_.-]+)\s*:(?![=])", line)
        if not match:
            continue
        target = match.group(1)
        if target.startswith(".") or "%" in target:
            continue
        targets.add(target)
    return sorted(targets)


def main() -> None:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    files = rg_files(ROOT)
    files = add_explicit_dirs(
        files,
        ROOT,
        [
            ROOT
            / "artifacts"
            / "sample_flagship"
            / "2025-10-30T18-39-31Z-a4ab8e7",
            ROOT / "artifacts" / "sample_wfv" / "2025-10-30T18-39-47Z-a4ab8e7",
        ],
    )

    inventory = repo_inventory(files)
    (GENERATED_DIR / "repo_inventory.json").write_text(
        json.dumps(inventory, indent=2, sort_keys=True), encoding="utf-8"
    )

    py_files = [ROOT / f for f in files if f.endswith(".py") and (
        f.startswith("src/") or f.startswith("experiments/") or f.startswith("tools/")
    )]

    sym_index = symbol_index(py_files)
    (GENERATED_DIR / "symbol_index.json").write_text(
        json.dumps(sym_index, indent=2, sort_keys=True), encoding="utf-8"
    )

    import_graph_data = import_graph(py_files)
    (GENERATED_DIR / "import_graph.json").write_text(
        json.dumps(import_graph_data, indent=2, sort_keys=True), encoding="utf-8"
    )

    targets = make_targets(ROOT / "Makefile")
    (GENERATED_DIR / "make_targets.txt").write_text("\n".join(targets) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
