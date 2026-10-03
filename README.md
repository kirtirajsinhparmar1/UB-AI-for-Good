# ACV Pulse

ACV Pulse combines WAV-based acoustic knock analysis with a prototype Acoustic Value Delta and ACV/Copart economics. Acoustic scoring and channel routing are calculated by the Python backend.

## Run locally

Start the backend from the repository root:

```sh
PYTHONPATH=backend uvicorn app.api.main:app --reload --port 8000
```

In another terminal, install the checked-in frontend dependencies and start Vite:

```sh
npm ci
npm run dev
```

The frontend defaults to `http://localhost:8000` for the backend. To change it, create `.env.local` in the repository root:

```sh
VITE_API_BASE_URL=http://localhost:8000
```

Vite exposes this value at build time. Restart the dev server after changing it. The backend's default CORS configuration includes Vite at `http://localhost:5173`.

## Demo flow

The Clean Engine Sample and Knocking Engine Sample buttons submit the real WAVs in `public/demo/` to `POST /v1/decision/analyze`. Both begin with the same editable economics: $15,000 base wholesale value, $14,200 Copart expected gross, $500 ACV costs, $700 Copart costs and a $500 minimum switch advantage. Upload accepts WAV files; live microphone capture is not enabled in this demo.

The acoustic knock score is a model score, not a calibrated probability or mechanical diagnosis. **Prototype economic policy for hackathon demonstration.** The displayed value adjustment is not ACV's current production pricing policy.

## Frontend checks

```sh
npm run lint
npm run build
```
