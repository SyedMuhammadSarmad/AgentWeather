# Learning Log: AgentWeather

After each session, add 3-5 lines: what I did, why, and what I'd get wrong if quizzed.

## Concept checklist (tick when I can explain it without notes)
- [ ] Why time series needs a time-based split (and what random splits leak)
- [ ] Shifting targets 24h ahead; why the newest 24h have no target
- [ ] Naive baseline (value 24h ago) and why every model must beat it
- [ ] RMSE vs MAE vs R2: what each tells me, when they disagree
- [ ] Imputation options (forward fill, interpolation, source fallback) and their trade-offs
- [ ] Fusing multiple sources: average vs priority vs separate features
- [ ] Time-based features and derived features (rate of change, rolling averages) without leakage
- [ ] Feature Store vs Model Registry: what each is for
- [ ] Statistical vs classical ML vs deep learning for forecasting: strengths and weaknesses
- [ ] One model per metric vs one multi-output model
- [ ] Why a new model replaces the current one only if validation improves
- [ ] SHAP/LIME: what the explanations mean and their limits
- [ ] Data drift vs model drift; how each is detected; what a threshold means
- [ ] LangGraph: nodes, shared state, edges; how state persists between runs
- [ ] LLM fallbacks and logging (latency, status, failures)
- [ ] Rule-based hazard alerts vs LLM-written alert text
- [ ] GitHub Actions: schedules, secrets, running scripts on cron and on a trigger

## Sessions
### 2026-11-19 to 2026-11-21 (Step 1: Project Rules, Concepts & Open-Meteo API Exploration)
- **Did:**
  - Reviewed project rules, non-negotiables, and the 11-step plan from `docs/AgentWeather_Project_Brief.md`.
  - Chose city: **Karachi** (`lat=24.8608`, `lon=67.0104`) and planned data sources: **Open-Meteo** (Weather Forecast + Archive + Air Quality) as primary + **OpenWeather Air Pollution** as 2nd source for fusion.
  - Set up `.gitignore` to keep `.env`, caches, venvs, and local data/models out of git.
  - Practiced the **5-step API schema exploration workflow** (skim docs -> raw `requests.get(..., timeout=15)` + `raise_for_status()` -> inspect `keys()` & `hourly_units` -> check sample values/types/nulls -> map to clean DataFrame).
  - Rewrote Open-Meteo exploration from scratch using plain `requests` + `pandas` (`pd.DataFrame(json_response["hourly"])`) instead of the `openmeteo_requests` SDK across Forecast Weather, Historical Weather Archive, and Air Quality endpoints.
  - Verified exact Open-Meteo units (`°C`, `%`, `mm`, `km/h`, `°`, `μg/m³`, `USAQI`), ISO 8601 timestamp parsing (`str` -> `datetime64[us, UTC]` via `pd.to_datetime(..., utc=True)`), and missingness (`df.isna().mean() * 100`).
- **Key findings & concepts learned:**
  - **Train/serve skew:** Training on one source (e.g., Open-Meteo AQI) and serving live on a different source (e.g., AQICN street sensor) creates a distribution mismatch that hurts accuracy and causes false data drift. Feed the exact same source(s) in training and live inference; live-only APIs (like AQICN) should only be fallbacks.
  - **Why backfill is required (not 24h live collection):** Shifting 24h ahead eats the newest 24 rows (so 24h of data = 0 labeled rows). Models (SARIMAX/Prophet, Random Forest, LSTM) need months of hourly history for training + time-based validation. Hourly job = ingest + Forecast Agent; Daily/drift job = Training pipeline.
  - **Features vs. Targets:** 6 metrics = **8 target columns** at `t + 24h` (`aqi`, `temp`, `precip_mm`, `rain_prob`, `humidity`, `uv`, `wind_speed`, `wind_dir`), created with `.shift(-24)`. Features (`X` at time `t`, past/present only): current readings + pollutants (`pm2_5`, `pm10`), cyclical encodings (`wind_dir_sin/cos`, `hour_sin/cos`, `month_sin/cos`), time features, lags (`1h`, `3h`, `24h`), rate of change (`diff_1h`, `diff_3h`), and rolling stats (`6h`, `24h`).
  - **`.shift(-24)` missing-hours trap:** `.shift(-24)` shifts by 24 *rows*, not 24 *hours*—missing hours silently misalign targets and lags. Always reindex onto a complete hourly grid (`freq="h"`) and impute before shifting/lagging.
  - **Source fusion & imputation:** Fusion = priority/fallback, average, or separate features. Imputation = forward-fill (`ffill`), linear interpolation, or same-hour averages. Ground stations (OpenAQ, Meteostat) can go offline; airport stations (Meteostat/Jinnah Airport) have high uptime but lack UV and rain probability.
  - **Open-Meteo quirks verified:**
    - Forecast Weather API: `0%` missing across all 7 weather columns.
    - Historical Weather Archive: `0%` missing for temp, humidity, precipitation, wind speed & direction; **`100%` missing** for `uv_index` and `precipitation_probability`; has a **~2–5 day delay** (requesting today/tomorrow UTC gives `400 Bad Request` -> backfill needs Archive for older dates + Forecast `past_days` for recent days).
    - Air Quality API: **`0%` missing** for `us_aqi`, `pm2_5`, `pm10`, and **`uv_index`** across historical dates (solves historical `uv_index`).
    - Historical `precipitation_probability` can be modeled via a binary target `will_rain = (precipitation > 0)` predicting probability.
  - **Debugging habits & bugs fixed:** Print `response.text` before `raise_for_status()` on `400` errors; always pass `timeout=15`; don't combine `past_days` with `start_date`/`end_date`; don't pass `hourly_units` (scalars) to `pd.DataFrame`; don't request weather variables from the Air Quality endpoint (`'undefined'`); watch unit differences across APIs (Open-Meteo wind is `km/h`, OpenWeather is `m/s`).
- **Would get wrong / still unsure (review before next quiz):**
  - What goes wrong when running `df['temp'].shift(-24)` with missing hours in the table (and how to prevent it).
  - Why linear interpolation (using hour before + hour after) cannot be used on the newest live hour.
  - Why we fetch and store timestamps in `UTC` instead of Karachi local time (`Asia/Karachi`).
  - Next to test: OpenWeather Air Pollution API schema & AQI scale (1–5 vs. Open-Meteo `us_aqi` 0–500).
