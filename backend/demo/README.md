# Offline demo runbook

The terminal comparator is the frontend emergency fallback. It runs the backend's real `analyze_knock(Path)` interface and the existing acoustic scorer. It never invents predictions and runs with Hugging Face offline mode enabled. The anomaly model is optional.

No engine recordings are included yet. Put real, readable WAV files in `backend/demo/sample_audio/` using these names:

```text
car_a.wav
car_b.wav
car_c.wav
```

Do not label recordings by engine condition unless that condition is known.

## Before demo day

Run these from the repository root while network access is available:

```sh
python backend/scripts/prefetch_models.py
python backend/scripts/preflight.py
```

Prefetch uses the free public Hugging Face repository `cxlrd/revix-AST-engine-knock` and its normal local cache. It can be rerun safely. Keep the same cache available to the OS user who runs the demo. Preflight is offline: it checks imports and cached assets and runs one real inference when dependencies, cached weights, and at least one readable demo WAV are available.

The model dependencies must be installed by the backend environment (Session A owns model implementation and dependency declarations). If a package is missing, prefetch and preflight print its name and stop without a traceback.

## Run the API offline

After a successful prefetch, start the API with offline mode enabled:

```sh
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONPATH=backend python -m uvicorn app.api.main:app --host 127.0.0.1 --port 8000
```

This keeps model loading local. The frontend can use the API as usual while the API is available.

## Emergency terminal comparison

If the frontend is unavailable, run the same real inference and scoring directly:

```sh
python backend/scripts/demo_compare.py \
  --vehicle "Car A" backend/demo/sample_audio/car_a.wav \
  --vehicle "Car B" backend/demo/sample_audio/car_b.wav \
  --vehicle "Car C" backend/demo/sample_audio/car_c.wav
```

Use 2–5 `--vehicle ID WAV` entries. Lowest acoustic risk is ranked first. To emit the existing API comparison contract as JSON, add `--json`. Use `--help` for CLI details.

The comparator validates each WAV before inference. Missing weights, invalid audio, or knock-model failures stop with a concise error. It does not download weights at presentation time, contact hosted inference, or upload audio.
