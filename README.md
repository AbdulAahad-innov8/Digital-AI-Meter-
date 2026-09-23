 Digital AI Meter — MLH Hackathon MVP

Working prototype with electricity/water dashboard, anomaly detection, prediction endpoint, possible leakage/fault insights, AI-style explanations, alerts, Ask AI, and time-slot analysis.

## Run on Windows
```powershell
cd digital-ai-meter
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Open **http://127.0.0.1:8000**.

The included meter data is simulated for a reliable hackathon demo. Leakage/fault messages indicate possible patterns, not confirmed physical faults. The AI explanation layer is local in this MVP, so no API key is required.
