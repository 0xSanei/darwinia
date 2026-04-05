# Security Policy

## Scope

Darwinia is a **simulation-only** framework. It does NOT execute real trades, connect to exchanges, or handle funds.

## What Darwinia does NOT do

- No network requests (runs entirely offline)
- No API keys or secrets required
- No cryptocurrency wallet integration
- No real order execution

## File access

Darwinia reads CSV data from `data/` and writes results to `output/`. It does not access files outside the project directory.

## Reporting a vulnerability

If you find a security issue, please open a [GitHub Issue](https://github.com/0xSanei/darwinia/issues) or email sanei@0xsanei.com.

## Dependencies

- numpy (numerical computation)
- pandas (data handling)
- streamlit + plotly (optional, dashboard only)
- pytest (dev only)

All dependencies are well-maintained, widely-used packages.
