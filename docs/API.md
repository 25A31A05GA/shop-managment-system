# REST API

Run: `python -m dukan_drishti serve --port 8080`. Add `?size=kirana|super|chain` to any call.

| Endpoint | Returns |
|---|---|
| `GET /api/health` | status, version |
| `GET /api/summary` | today's sales, bills, branches needing a check |
| `GET /api/branches` | each branch with a traffic-light status |
| `GET /api/forecast` | 14-day forecast, range, back-test miss |
| `GET /api/stock?cover=7&uplift=1` | what to reorder and how much |
| `GET /api/brands` | in-demand and slow brands, with reasons |
| `GET /api/sources?i=0` | fair test of two supply sources (`i` 0 to 3) |
| `GET /api/offers` | each offer's extra sales vs discount given |
| `GET /api/suppliers` | supplier reliability |
| `GET /api/khata` | credit owed and ageing |
| `GET /api/expiry` | stock about to expire |
| `GET /api/profit` | what the owner really keeps, break-even per day |
| `GET /api/cash` | cash drawer checks |
| `GET /api/price` | prices against the market |
| `GET /api/history?kind=weekly` | `daily`, `weekly`, `monthly` or `yearly` |
| `GET /api/roles` | who may see what |
| `GET /api/search?q=horlix` | typo-tolerant search |
| `GET /api/ask?q=which brand sells least` | plain-English answer plus how it was worked out |
| `GET /api/brief` | the owner's morning brief |

Browsers get a styled page at `/`; programs get JSON. Errors: `400` bad input, `404` not found, `500` with a message (never a stack trace).

```bash
curl "http://localhost:8080/api/search?q=sona%20masuri"
```
