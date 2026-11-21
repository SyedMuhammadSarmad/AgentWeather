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


### 2026-11-21 Afternoon (Deep-Dive on Open-Meteo Endpoints, Rain Probability & Backfill vs. Hourly Pipeline)
- **Did:**
  - Walked through all 3 Open-Meteo exploration scripts one by one (`explore_openmeteo.py`, `explore_openmeteo_historical_weather.py`, `explore_openmeteo_air_quality.py`) to understand every parameter and how each endpoint fits into training vs. live forecasting.
- **Key findings & concepts learned:**
  - **What `json_response["hourly"]` brings:** A dictionary of equal-length lists (`time` + each requested variable) where each index lines up across keys, so `pd.DataFrame(json_response["hourly"])` turns each key into a column and each index into an hourly row.
  - **Forecast endpoint (`v1/forecast`) params & cutoff:**
    - `relative_humidity_2m` is standard Humidity (%) measured at 2 meters above ground.
    - `past_days` controls how many past full days to fetch (max `92`); in hourly live runs we use `past_days=2` (48 past hours) so 24h lags and rolling averages compute cleanly with no `NaN`s.
    - `forecast_days=1` includes today's 24 hours (`00:00`–`23:00` UTC). Because it includes future hours of today, our code must truncate them with `df = df[df["time"] <= pd.Timestamp.now(tz="UTC").floor("h")]` (e.g., at 5:54 PM, keep rows up to 5:00 PM and drop 6:00 PM onward).
  - **Historical Weather (`archive-api`) + Air Quality (`air-quality-api`) merge:**
    - Archive Weather covers older months (temp, humidity, precipitation, wind speed & direction) up to ~5 days ago; Forecast `past_days` stitches on the last ~5 days.
    - Air Quality (`air-quality-api`) has **both** history and live (`us_aqi`, `pm2_5`, `pm10`, `uv_index`) with no 5-day delay; merging it with Weather on `time` (UTC) supplies `uv_index` for every historical hour.
  - **Rain probability without a historical `precipitation_probability` feature:** Like a spam filter, we don't need `precipitation_probability` as an input feature during training or live runs. Historical weather records whether it rained (`precipitation > 0` -> `1`, else `0`); training a classifier on that binary target and calling `predict_proba` outputs rain probability (0–100%), keeping training and live features 100% identical.
  - **Backfill vs. Hourly Pipeline:**
    - **Backfill:** Runs **once** at the start to load months of historical hourly rows into Hopsworks for EDA and initial model training.
    - **Hourly Pipeline:** Runs **every hour** via GitHub Actions to append 1 new row (using ~48 past hours to compute 24h lags/rolling stats) so the Forecast Agent can predict 24h ahead.
    - Both reuse the **exact same** cleaning, fusion, imputation, and feature-engineering code—only the date range changes.
  - **Defensive overlap & deduplication (`Archive` + `Forecast`):**
    - Intentionally overlap Archive Weather and Forecast Weather (`past_days=7`) by 1–2 days instead of risking a 24h gap from off-by-one/timezone bugs.
    - Make sure both DataFrames have the exact same columns, stack with Archive first (`pd.concat([archive_df, forecast_df], ignore_index=True)`), then deduplicate (`drop_duplicates(subset=["time"], keep="first")`), sort by `time`, and check `assert df["time"].is_unique`.
    - **Why Archive wins (`keep="first"`):** Archive (ERA5 reanalysis) is verified 2–5 days later by ECMWF using real stations, balloons, ships, and satellites—making it closer to ground truth than Forecast API's real-time run, which we only use for the newest ~5 days and live hours.
- **Would get wrong / still unsure (review before next quiz):**
  - Why we fetch and store timestamps in `UTC` instead of Karachi local time (`Asia/Karachi`).
  - Next step: test **OpenWeather Air Pollution API** (`scripts/explore_openweather.py`) to finish Step 1.

### 2026-11-22 (Time-Series Foundations Locked In: Shifting, Hourly Grid, Imputation & UTC)
- **Did:**
  - Walked through every detail of `.shift(-24)`, hourly grid reindexing (`asfreq("h")`), linear interpolation vs. forward-fill (`ffill`), UTC timestamps, and production repo layout (`src/` by pipeline stage).
- **Key concepts locked in:**
  - **Why & where `.shift(-24)` happens:** `model.fit(X, y)` needs today's features (`X`) and tomorrow's real answer (`y`) side-by-side on the same row. `.shift(-24)` runs in the **Training Pipeline** (and EDA), not the hourly Feature Pipeline. Every day, the newest 24 rows have `NaN` targets until the next 24 hours arrive (e.g., at Nov 21 12:00 AM, Nov 20's 24 rows have `NaN` targets; at Nov 22 12:00 AM, Nov 21's data gives Nov 20 its real targets while Nov 21's 24 rows wait with `NaN`).
  - **Preventing missing-hour shift bugs (5-step pandas pattern):**
    `df = df.sort_values("time").set_index("time").asfreq("h").ffill(limit=6).reset_index()`
    (`asfreq("h")` inserts `NaN` rows for any skipped clock hours so every consecutive row is strictly 1 hour apart before computing lags, rolling averages, or `.shift(-24)`).
  - **Linear interpolation vs. Forward-fill (`ffill(limit=6)`):**
    - Linear interpolation draws a straight line between a point *before* and a point *after* a gap. It cannot work on the newest live hour (right now) because the future hour after it hasn't happened yet—and using it on training history peeks into the future (data leakage).
    - `ffill(limit=6)` only uses past data (safe for both training and live with zero leakage) and caps filling at 6 hours so a long outage doesn't copy 2 PM's 36°C into 3 AM; outages > 6h fall back to the 2nd API or same-hour past average.
  - **Why UTC everywhere:** OpenWeather, Hopsworks, and GitHub Actions all use UTC—keeping ingestion, storage, and training in UTC prevents silent 5-hour misalignment and DST bugs. Convert to `Asia/Karachi` (`UTC+5`) only for dashboard/report display.
  - **Repo layout plan:** Keep exploration scripts in `scripts/`, and put production code under `src/` organized by pipeline stage (`ingestion/`, `features/`, `training/`, `agents/`).
- **Next step:**
  - Test **OpenWeather Air Pollution API** (`scripts/explore_openweather.py`) with `.env` + `python-dotenv` to finish Step 1.
