# Waste & Methane Monitoring Lab V1.0

Independent educational Python prototype for **COP31 AI Solutions Lab — Day 3 (November 11, 2026)**.

> **Not an official COP31 application or a validated methane emissions inventory.** The included dataset is synthetic. The methane coefficient and GWP values are user-configurable *illustrative scenario assumptions*, **not sourced or certified emission factors**. Do not use the results for regulatory reporting, emissions accounting, or claims of avoided methane.

## Five modules

1. **Overview** — waste quantities and source data.
2. **Waste & Methane Indicators** — transparent waste routing and illustrative methane/CO₂e proxy equations.
3. **Trends & Alerts** — charts and configurable period-to-period threshold flags.
4. **Gemini AI Interpretation** — optional real Gemini 2.5 Flash API request for structured interpretation; requires a key and human review.
5. **Human Review & Export** — explicit review decisions saved in SQLite and CSV/JSON downloads.

## Windows / PyCharm setup

Install **Python 3.11 or 3.12**. Open this folder in PyCharm's terminal (PowerShell):

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest -q
python -m streamlit run app.py
```

If PowerShell blocks activation, use `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` and then the same Python executable for pytest and Streamlit.

Streamlit will show a local URL, usually `http://localhost:8501`. The included CSV loads automatically; no network connection is needed for the deterministic modules.

### Enable real Gemini 2.5 Flash (optional)

```powershell
Copy-Item .env.example .env
```

Open `.env` and replace the placeholder with your actual `GEMINI_API_KEY`. Restart Streamlit, open **Gemini AI Interpretation**, and click **Generate AI interpretation**. The key is never committed; `.env` is ignored by Git. External API calls may incur costs. Only aggregated indicators, alerts, scenario assumptions, an ordered period summary (period labels, aggregate waste quantities and signed changes), and a SHA-256 hash are sent; the raw uploaded CSV is not sent. The model's output is *unverified* until reviewed.

## CSV input

Required columns: `period,waste_tonnes,landfill_fraction,recycling_fraction,compost_fraction`. Fractions must be between 0 and 1, with combined destination fractions no greater than 1. Remaining mass is labeled `other_tonnes`. Rows are analyzed in file order; sort periods before uploading.

## Scientific limitations

- The methane calculation is a **toy linear sensitivity proxy**, not an IPCC first-order decay model.
- It excludes waste composition, degradable carbon, historical disposal, decay rates, gas recovery, oxidation, and site-specific measurements.
- It assumes landfill methane production is proportional to the current period's landfilled mass, which is **not physically realistic for inventory use**.
- GWP and methane coefficient defaults are illustrative inputs, not claims of official applicability.
- Period-to-period alerts are simple threshold rules, not statistically validated anomaly detection.
- The AI does not validate source documents or certify calculations. Human review decisions are logged, not independently verified.
- SQLite `data/reviews.sqlite3` is created locally and is **not** included in the source distribution.

## Reproducibility and release status

Run `python -m pytest -q` for deterministic unit tests. To validate the live integration, add your own API key, execute the Gemini tab, inspect its structured JSON, and save a human review. Record evidence before claiming live AI success. Do not publish API keys or the SQLite database.

**Evidence first. Engineering second. Measurable impact as the goal.**

## V1.0 release refinements

- Gemini receives a compact **period context** with six ordered monthly waste totals (for the bundled example), the previous period, the signed percentage change, and the direction (increase/decrease). This addresses a manual-test finding in which the model incorrectly claimed that no time series existed. The model may still make mistakes; review remains mandatory.
- JSON and CSV exports round floating-point display artifacts to six decimal places, while the underlying calculations and SHA-256 input fingerprint remain unchanged. Exported values are suitable for readable demonstration, not certified precision.
- A signed March change of **+44%** (125 to 180 tonnes) is supported by the bundled synthetic dataset. The alert is a threshold rule, not evidence of a real environmental event.

## Test evidence and methodology

- Local functional testing on Windows/PyCharm was reported for the five tabs, illustrative calculations, 30% vs 5% alert sensitivity, real Gemini 2.5 Flash API response, human review, three exports, and SQLite persistence after restart. The model response contained a time-series interpretation error, which motivated the context correction above. **The corrected AI prompt still needs a new live API test** to establish the improvement.
- Run `python -m pytest -q` to reproduce the automated tests. Tests cover deterministic logic and local SQLite operations; they do **not** exercise the paid/live Gemini endpoint.
- Synthetic scenario defaults: 25 kg illustrative CH4 per landfilled tonne and hypothetical GWP100 of 27. CO2e proxy (t) = landfilled tonnes × 25 × 27 / 1000. These are not an IPCC landfill inventory.
- Source control intentionally excludes `.env`, `.venv`, `data/*.sqlite3`, real keys, and personal audit data. Only the synthetic sample CSV is included.
