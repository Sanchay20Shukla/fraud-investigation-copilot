# API guide

[Back to the project overview](../README.md)

Start the backend from the repository root:

```bash
python -m uvicorn api.main:app --host 127.0.0.1 --port 8010
```

Interactive OpenAPI documentation is available at `http://127.0.0.1:8010/docs`. Bootstrap the database, model and index before calling investigation endpoints.

## Investigate a transaction

```bash
curl -X POST http://127.0.0.1:8010/investigate \
  -H "Content-Type: application/json" \
  -d '{"transaction_id":"TXN_0000002"}'
```

PowerShell equivalent:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8010/investigate `
  -ContentType application/json -Body '{"transaction_id":"TXN_0000002"}'
```

The response contains an investigation UUID, the transaction, model probability and score, signed SHAP contributions, a recommendation, observed indicators, history, policy citations, limitations and workflow stages. See the [recorded sample response](../reports/sample_investigation.json). Scores depend on the trained model and dataset; that sample is not a promised result for generated demo data.

## Conversational follow-up

```python
import httpx

base = "http://127.0.0.1:8010"
with httpx.Client(base_url=base, timeout=60) as client:
    response = client.post("/chat", json={"question": "Investigate TXN_0000002"})
    response.raise_for_status()
    case = response.json()

    response = client.post("/chat", json={
        "question": "Show previous transactions for this account",
        "session_id": case["session_id"],
    })
    response.raise_for_status()
    print(response.json())
```

Omit `session_id` to start a new conversation. Reuse the returned UUID to retain the transaction context. A fresh conversation asking about “this account” will request a transaction ID first. Session tokens are for a single-user demo and are not an authentication system.

## Routes

| Method | Path | Behavior |
|---|---|---|
| GET | `/health` | Check process liveness |
| GET | `/ready` | Check artifact initialization and transaction availability |
| GET | `/transactions/{transaction_id}` | Retrieve a transaction without training labels |
| POST | `/investigate` | Generate and save an evidence-based report |
| POST | `/chat` | Route a question and optionally retain conversation context |
| GET | `/investigations/{investigation_id}` | Retrieve a saved report |

## Input and error behavior

- Transaction IDs use `TXN_` plus exactly seven digits.
- Questions must contain 1–2,000 characters.
- Ask about one transaction at a time.
- Missing records return HTTP 404; malformed requests return 400 or 422.
- Unsupported questions receive an insufficient-evidence answer.
- Missing initialization artifacts return HTTP 503.
- No route accepts arbitrary SQL or performs account actions.

History and counterparty queries use earlier time steps in the loaded data. Empty results do not establish that an account is new or that no other transactions exist.
