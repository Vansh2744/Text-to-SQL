# API (`/api/v1`, errors: `{"error": {"code", "message"}}`)

| Method | Path | Notes |
|---|---|---|
| GET | /health, /health/ready | readiness checks DB + storage |
| GET | /dashboard | counts + recent items |
| POST | /datasets/upload | multipart `file` |
| GET | /datasets, /datasets/{id}, /{id}/schema, /{id}/preview, /{id}/profile | |
| PATCH/DELETE | /datasets/{id} | rename / delete (cascades) |
| POST | /queries/analyze | `{dataset_id, question, conversation_id?}` -> SQL, rows, chart, explanation |
| POST | /queries/execute | `{dataset_id, sql}` edited SQL, same validation |
| GET | /queries/history, /queries/{id} | |
| POST | /queries/{id}/rerun | |
| POST/GET | /conversations, /conversations/{id} | |
| POST | /conversations/{id}/messages | follow-up question |
| DELETE | /conversations/{id} | |
| CRUD | /saved-queries, POST /saved-queries/{id}/run | SQL re-validated on every run |

Auth: `Authorization: Bearer <Clerk JWT>` (or `X-Dev-User` in dev mode). Interactive docs at `/docs`.
