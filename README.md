# Contact Identifier API

A Flask backend service for identifying and linking contacts using SQLite and SQLAlchemy, managed with uv.

## Requirements
- Python 3.8+
- [uv](https://github.com/astral-sh/uv) (for dependency management)

## Setup

```sh
uv venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
uv pip install -r requirements.txt  # or: uv pip install .
```

## Running the server

```sh
python main.py
```

## Seeding
On startup, the DB is seeded with an example contact.

## API
### POST `/identify`

Request JSON:
```json
{
  "email": "user@example.com",   // optional
  "phoneNumber": "+1234567890"   // optional
}
```
At least one of `email` or `phoneNumber` is required.

#### Example curl:
```sh
curl -X POST http://localhost:5000/identify \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "phoneNumber": "+1234567890"}'
```

#### Example response:
```json
{
  "contact": {
    "primaryContatctId": 1,
    "emails": ["user@example.com"],
    "phoneNumbers": ["+1234567890"],
    "secondaryContactIds": [2, 3]
  }
}
```

### Error Handling
- If both `email` and `phoneNumber` are missing, returns 400.

## Notes
- All timestamps are in UTC.
- No hard-coded paths are used.

---
