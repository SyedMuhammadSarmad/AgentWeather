---
trigger: always_on
---

# Project Context: AgentWeather

I'm a data science intern at 10Pearls (SHINE Internship, Cohort 10, 2026). This project is graded through project-based learning and quizzes, so my understanding matters more than speed.

Full brief: docs/AgentWeather_Project_Brief. Read it when you need requirements, deliverables or details. Don't assume anything that isn't in it.

## What we're building
AgentWeather: an agentic multi-metric weather and AQI forecasting system on a managed serverless stack. It forecasts 6 metrics 24 hours ahead for one city, with a LangGraph agent layer on top that writes alerts and a news-style report and watches for drift.

Metrics: AQI, temperature (C), precipitation (mm and rain probability), humidity (%), UV index, wind (speed and direction). Evaluation: RMSE, MAE, R2.

## Stack (from the brief)
- Python; data from any weather/AQI API (e.g. OpenWeather, AQICN)
- Hopsworks free tier: Feature Store (features, raw data, logs) and Model Registry
- Models: at least 3 from different families (statistical e.g. SARIMAX/Prophet; classical ML e.g. Ridge/Random Forest; deep learning e.g. LSTM) + naive baseline (value 24h ago)
- Explainability: SHAP, LIME or similar
- Agents: LangGraph, 4 agents sharing one state saved in the Forecast Ledger; LLM for Alert and Weather Report agents (any LLM, e.g. Groq free API, with fallbacks)
- CI/CD: GitHub Actions (ingestion hourly; training daily and on drift)
- Dashboard: Streamlit Community Cloud, HuggingFace Spaces or Render

## My choices (fill in as decided)
- City: Karachi, Pakistan (lat=24.8608, lon=67.0104; timestamps stored in UTC)
- Data sources and fusion strategy: Open-Meteo (Weather Forecast + Historical Weather Archive + Air Quality for weather, us_aqi, uv_index, pm2_5, pm10) + OpenWeather Air Pollution API (history + live for backup pm2_5/pm10 and extra gases co, no2, o3, so2). Fusion: Source Priority (Open-Meteo primary, OpenWeather fallback via fillna on pm2_5/pm10; keep Open-Meteo us_aqi 0-500 scale separate from OpenWeather 1-5 scale; Archive wins over Forecast on 1-2 day overlap via drop_duplicates keep="first").
- Imputation strategy: Reindex onto complete hourly UTC grid (asfreq("h")), forward-fill past-only up to 6 hours (ffill(limit=6)), fallback to secondary source or same-hour past average for gaps > 6h (no linear interpolation to avoid future leakage).
- One model per metric or one for all six: [TBD]
- Models chosen: [TBD]
- LLM + fallback: [TBD]
- Dashboard host: [TBD]

## Pipelines and agents (summary)
- Feature pipeline (hourly): fetch, fuse and time-align, impute, compute features (time-based + derived such as rate of change and rolling averages), store in the Feature Store. Backfill reuses the same script for past dates; targets come from shifting observations 24h ahead; the newest 24h have no target and are used for forecasting only.
- Training pipeline (daily and on drift): fetch features/targets, train and evaluate with a time-based split, store in the Model Registry; a new model replaces the current one only if it scores better on validation.
- Forecast agent (hourly): latest features + best model, 24h forecast per metric, saved to the Feature Store.
- Alert agent: fixed rules check hazards across all six metrics; if triggered, an LLM writes alerts for the general public, sensitive groups and outdoor workers.
- Weather Report agent (daily and after a new alert): news-style report from forecasts and alerts.
- Drift agent: data drift (live vs training features) and model drift (recent error vs validation error); alerts the team and triggers extra training above a threshold.
- Logs in the Feature Store: Forecast Ledger, Agent call log (prompt, response, latency, status; failures form the failure log), Drift log.

## Deliverables
1. End-to-end automated forecasting system with a working agentic layer.
2. Deployed dashboard styled as a weather report: 24h forecasts for all six metrics, news-style report, Agent Activity panel (alerts), EDA and SHAP/LIME explanations, drift events and metrics, failed agent calls.
3. Report: sources, imputation, model choices, issues and fixes, agent performance (alert quality, drift detection, LLM call failures).
Also required: thorough EDA on each metric before modelling; explainability; hazard alerts for all metrics.

## Suggested work order (guide me through it, one step at a time)
1. Pick the city and data sources; explore the APIs
2. Feature pipeline: fetch, fuse, impute, features; store in Hopsworks
3. Backfill history; create 24h-ahead targets
4. EDA on each metric
5. Baseline, then 3+ models; time-based split; RMSE/MAE/R2 per metric
6. Model Registry logic (replace only if better)
7. SHAP/LIME explanations
8. LangGraph agents: Forecast, Alert, Weather Report, Drift; logging; LLM fallbacks
9. GitHub Actions: hourly ingestion, daily training, drift-triggered training
10. Dashboard and deployment
11. Final report

## Learning
Keep LEARNING.md updated. At the end of each session, quiz me on the concepts used that day.
