# Mobile self-inspection API

The module analyzes consumer engine recordings with the existing local
`analyze_knock(Path)` model interface. The mobile endpoint accepts multipart
WAV uploads only. Production could add mobile codec normalization; hackathon
MVP accepts WAV.

## Request

`POST /v1/self-inspection/analyze` with multipart fields:

```text
vehicle_id=<id>
audio_file=<wav>
```

Example using curl:

```sh
curl -X POST http://localhost:8000/v1/self-inspection/analyze \
  -F 'vehicle_id=vehicle-123' \
  -F 'audio_file=@engine.wav;type=audio/wav'
```

## Response

```json
{
  "vehicle_id": "vehicle-123",
  "filename": "engine.wav",
  "capture": {
    "duration_seconds": 4.0,
    "sample_rate": 48000,
    "channels": 1,
    "quality_status": "good",
    "quality_warnings": []
  },
  "acoustic": {
    "knock_probability": 0.12,
    "acoustic_risk_score": 12,
    "risk_band": "low",
    "model_name": "local-knock-model"
  },
  "status": "ready"
}
```

`acoustic_risk_score` reuses the existing score (`round(knock_probability * 100)`).
The `risk_band` is `low` through 33, `medium` through 66, and `high` above 66.
Use **Low acoustic risk** for `low`; `medium` and `high` indicate **Elevated
acoustic risk**. These labels describe the audio result, not an engine diagnosis.

Capture checks use WAV metadata only. Clips shorter than 2 seconds and clips
longer than 30 seconds return a warning; captures may not exceed 60 seconds or
fall below an 8 kHz sample rate. Stereo audio is accepted. Invalid WAV files,
unsupported formats, unusable sample rates, and overlong captures return HTTP
400. Uploads over the configured size limit (10 MiB by default) return HTTP
413. Every stored temporary upload is deleted after processing, including
error responses.

## Router integration

The router is intentionally not mounted in `app.api.main`. The application
integrator can add it with:

```python
from app.api.self_inspection_router import router as self_inspection_router

app.include_router(self_inspection_router)
```
