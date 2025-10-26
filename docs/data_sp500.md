# Data Inventory: data_sp500/

A quick audit of the bundled S&P 500-style panel (`data_sp500/`) produced the following snapshot (see `reports/data_inventory_sp500.json` for the full dump):

- **936** per-symbol CSVs (`timestamp`, `close`, `volume`).
- **Global coverage:** 2005-01-03 through 2024-12-31 (daily frequency).
- **Average length:** ~3,752 rows per symbol.
- **Missing `volume`:** 19 tickers exhibit gaps (notably AAL, BPYU, COOP). Clean or forward-fill before running executions that depend on volume.
- **Non-positive `volume`:** 10 tickers contain zero/negative prints (e.g., ABMD, BTU). These should be filtered or corrected during preprocessing.

### Next-step Checks
- Validate holiday calendars and ensure no forward-looking dates slip in.
- Join with a constituent metadata table (sectors, market cap, share count) to enforce universe filters and neutralization.
- Consider trimming defunct tickers once they delist to avoid unrealistic OOS signals.

The audit was generated via:

```bash
python3 - <<'PY'
from pathlib import Path
import pandas as pd
import json

root = Path('data_sp500')
files = sorted(root.glob('*.csv'))
summary = []
missing_volume_symbols = []
nonpos_volume_symbols = []
for path in files:
    df = pd.read_csv(path)
    date_col = df.columns[0]
    df[date_col] = pd.to_datetime(df[date_col])
    summary.append({
        'symbol': path.stem,
        'start': df[date_col].min().strftime('%Y-%m-%d'),
        'end': df[date_col].max().strftime('%Y-%m-%d'),
        'rows': len(df),
        'missing_close': int(df['close'].isna().sum()),
        'missing_volume': int(df['volume'].isna().sum()),
        'nonpos_volume': int((df['volume'] <= 0).sum()),
    })
    if df['volume'].isna().any():
        missing_volume_symbols.append(path.stem)
    if (df['volume'] <= 0).any():
        nonpos_volume_symbols.append(path.stem)

Path('reports/data_inventory_sp500.json').write_text(json.dumps({
    'total_symbols': len(files),
    'summary': summary,
    'missing_volume': missing_volume_symbols,
    'nonpos_volume': nonpos_volume_symbols,
}, indent=2))
PY
```

(Already executed and committed so you don’t have to rerun unless the panel changes.)
