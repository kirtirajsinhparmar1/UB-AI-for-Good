# Acoustic Intelligence Backend

FastAPI backend for local engine acoustic analysis and vehicle disposition decisions. The AST knock model runs from cached local weights; the backend does not fetch market prices. Callers provide ACV wholesale and Copart estimates.

## Run

```sh
python -m pip install -r backend/requirements.txt
PYTHONPATH=backend python -m uvicorn app.api.main:app --reload
```

The interactive API schema is available at `/docs`.

## Full disposition decision

`POST /v1/decision/analyze` accepts `multipart/form-data`:

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `vehicle_id` | string | yes | Vehicle identifier |
| `audio_file` | WAV file | yes | Engine audio recording |
| `base_wholesale_value` | number | yes | Starting ACV wholesale estimate; must be greater than zero |
| `copart_expected_gross` | number | yes | Copart gross estimate supplied by the caller |
| `minimum_switch_advantage` | number | no | Defaults to `500` |

The response contains `acoustic`, `valuation`, `economics`, and `decision` objects. `acoustic_knock_score` is a 0–100 score, not a calibrated probability. `valuation.acoustic_delta_pct` is a fractional rate (for example, `0.00325` means a `0.325%` adjustment). The bundled policy is always identified as `prototype_demo_policy`; it is illustrative and requires empirical calibration before production use. Economics compares Adjusted ACV Value (`economics.acv_expected_value`) with Copart Expected Value (`economics.copart_expected_value`) directly. `economics.value_difference` is Copart minus ACV. `decision.recommended_channel` is `ACV`, `COPART`, or `REVIEW`; `decision_strength` describes the configured value-margin rule, not statistical confidence.

Example request:

```sh
curl -X POST http://localhost:8000/v1/decision/analyze \
  -F 'vehicle_id=vehicle-a' \
  -F 'audio_file=@backend/demo/sample_audio/car_clean_0006.wav;type=audio/wav' \
  -F 'base_wholesale_value=15000' \
  -F 'copart_expected_gross=14200' \
  -F 'minimum_switch_advantage=500'
```

Example JSON response:

```json
{
  "vehicle_id": "vehicle-a",
  "acoustic": {
    "acoustic_knock_score": 27,
    "risk_band": "low",
    "model_name": "cxlrd/revix-AST-engine-knock"
  },
  "valuation": {
    "base_wholesale_value": 15000,
    "acoustic_delta_pct": 0.00325,
    "acoustic_delta_amount": 48.75,
    "adjusted_wholesale_value": 15048.75,
    "policy_type": "prototype_demo_policy",
    "policy_version": "demo-v1",
    "policy_note": "Illustrative hackathon policy. Replace with empirically calibrated ACV/Copart historical outcomes in production."
  },
  "economics": {
    "acv_expected_value": 15048.75,
    "copart_expected_value": 14200,
    "value_difference": -848.75
  },
  "decision": {
    "recommended_channel": "ACV",
    "decision_strength": "strong",
    "minimum_switch_advantage": 500,
    "rationale": "Adjusted ACV value exceeds Copart expected value by $848.75, meeting the $500 routing threshold."
  },
  "disclaimer": "Prototype economic policy for hackathon demonstration; production values require empirical calibration."
}
```

## Self-inspection

`POST /v1/self-inspection/analyze` accepts multipart fields `vehicle_id` (string) and `audio_file` (WAV). It returns capture-quality information and the existing local acoustic assessment contract.

## Errors

- `400`: invalid vehicle ID, WAV, or economic value (`invalid_audio`, `invalid_base_wholesale_value`, `invalid_copart_expected_gross`, and related field codes).
- `413`: upload exceeds the configured `ACOUSTIC_MAX_UPLOAD_BYTES` limit (default 10 MiB).
- `422`: missing or malformed multipart fields.
- `500`: local inference or decision processing failed.
- `503`: local knock model or cached weights are unavailable.

Uploaded WAV files are deleted after analysis. Run the tests with:

```sh
PYTHONPATH=backend python -m pytest backend -q
```

The canonical demo recordings are `demo/sample_audio/car_clean_0006.wav` and `demo/sample_audio/car_knocking_0003.wav`; `car_knocking_0024.wav` is retained as an alternate knock sample.
