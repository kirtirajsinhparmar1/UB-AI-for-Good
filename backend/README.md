# Acoustic Intelligence Backend

Small WAV-only backend contract for engine audio analysis. Knock and anomaly inference are explicit stubs; the API returns a structured `503 model_not_ready` response until Session A implements knock inference. No model weights or predictions are included.

## Run

```sh
python -m pip install -r backend/requirements.txt
PYTHONPATH=backend python -m uvicorn app.api.main:app --reload
```

Health check: `GET /health`. The prepared upload routes are `POST /v1/audio/analyze` (`file`, optional `vehicle_id` multipart fields) and `POST /v1/audio/compare` (`files` multipart field). Comparison ranking uses the term **lowest acoustic risk**.

Scores currently use `round(knock_probability * 100)`: 0–33 is `low`, 34–66 is `medium`, and 67–100 is `high`. The optional anomaly signal does not affect the MVP score.

## Verify

```sh
python -m pip install -r backend/requirements-test.txt
PYTHONPATH=backend python -m pytest backend/tests -q
PYTHONPATH=backend python backend/scripts/preflight.py
```

## Parallel ownership

- **Session A — Knock Model:** owns `backend/app/model/knock_model.py` and any knock-specific preprocessing module it adds. Use the shared WAV validator; do not edit the API or shared contracts.
- **Session B — General Acoustic Anomaly:** owns `backend/app/model/anomaly_model.py` and any anomaly-specific preprocessing module it adds. The signal is optional and must not block knock scoring.
- **Session C — API:** owns `backend/app/api/main.py` and API-specific modules under `backend/app/api/`. Keep the established result and comparison shapes.
- **Session D — Demo / Hardening:** owns `backend/scripts/`, `backend/demo/sample_audio/`, and `backend/tests/`.
- **Final integration:** may modify all files after the parallel work is complete.

Shared contracts are `backend/app/schemas.py`, `backend/app/scoring/acoustic_score.py`, `backend/app/model/audio_io.py`, and `backend/app/model/__init__.py`. Coordinate before changing these; parallel sessions should avoid editing each other's files.
