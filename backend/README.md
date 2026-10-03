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
| `acv_costs` | number | no | Defaults to `0` |
| `copart_costs` | number | no | Defaults to `0` |
| `minimum_switch_advantage` | number | no | Defaults to `500` |

The response contains `acoustic`, `valuation`, `economics`, and `decision` objects. `acoustic_knock_score` is a 0–100 score, not a calibrated probability. `valuation.acoustic_delta_pct` is a fractional rate (for example, `0.00325` means a `0.325%` adjustment). The bundled policy is always identified as `prototype_demo_policy`; it is illustrative and requires empirical calibration before production use. `economics.net_difference` is Copart net minus ACV net. `decision.recommended_channel` is `ACV`, `COPART`, or `REVIEW`; `decision_strength` describes the configured net-margin rule, not statistical confidence.

Example request:

```sh
curl -X POST http://localhost:8000/v1/decision/analyze \
  -F 'vehicle_id=vehicle-a' \
  -F 'audio_file=@backend/demo/sample_audio/car_clean_0006.wav;type=audio/wav' \
  -F 'base_wholesale_value=15000' \
  -F 'copart_expected_gross=11000' \
  -F 'acv_costs=500' \
  -F 'copart_costs=700'
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
    "acv_expected_gross": 15048.75,
    "acv_costs": 500,
    "acv_expected_net": 14548.75,
    "copart_expected_gross": 11000,
    "copart_costs": 700,
    "copart_expected_net": 10300,
    "net_difference": -4248.75
  },
  "decision": {
    "recommended_channel": "ACV",
    "decision_strength": "strong",
    "minimum_switch_advantage": 500,
    "rationale": "ACV expected net exceeds Copart expected net by $4,248.75, meeting the $500 routing threshold."
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
