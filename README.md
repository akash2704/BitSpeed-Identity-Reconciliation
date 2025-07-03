# Contact Identifier API

A Flask backend service for identifying and linking contacts using SQLite and SQLAlchemy, managed with [uv](https://github.com/astral-sh/uv).

## Requirements
- Python 3.8+
- [uv](https://github.com/astral-sh/uv) (dependency manager)

## Setup

1. **Clone the repository and enter the directory:**
   ```sh
   git clone <repo-url>
   cd bitspeed
   ```
2. **Install dependencies using uv:**
   ```sh
   uv sync --locked
   ```
   *(This uses `pyproject.toml` and `uv.lock` for reproducible installs)*

3. **Environment variables:**
   - Copy `.env` (provided) and edit as needed.
   - Example:
     ```ini
     FLASK_ENV=production
     FLASK_DEBUG=0
     DATABASE_URL=sqlite:///contacts.db
     # SECRET_KEY=your_secret_key_here
     ```

## Running the server

```sh
uv run main.py
```
The server will start (by default on port 5000). On startup, the DB is seeded with an example contact if empty.

## API
### POST `/identify`

**Request JSON:**
```json
{
  "email": "user@example.com",   // optional
  "phoneNumber": "+1234567890"   // optional
}
```
*At least one of `email` or `phoneNumber` is required.*

**Example curl:**
```sh
curl -X POST http://localhost:5000/identify \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "phoneNumber": "+1234567890"}'
```

**Example response:**
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

**Error Handling:**
- If both `email` and `phoneNumber` are missing, returns HTTP 400.

## Docker
To build and run with Docker:
```sh
docker build -t contact-identifier .
docker run -p 8002:8002 contact-identifier
```
Then use `http://localhost:8002/identify` for API calls.

## Notes
- All timestamps are in UTC.
- No hard-coded paths are used.
- Secrets and configuration should be placed in `.env` (never commit secrets!).

---
