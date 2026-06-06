# Content Upload & Review System

A Flask + MongoDB service for the content team to **upload movie data via CSV**
(up to 1 GB) and **query it** with pagination, filtering, and sorting.

---

## Tech stack
- **Python 3.12**, **Flask** (REST API)
- **MongoDB** (storage) via **PyMongo**
- **pytest** + **mongomock** for tests (no live DB needed to run them)

---

## Setup

```bash
# 1. Create and activate an environment
conda create -n curs python=3.12 -y
conda activate curs

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env          # then edit if your Mongo isn't on localhost:27017

# 4. Make sure MongoDB is running locally (default mongodb://localhost:27017)

# 5. Run
python run.py                 # serves on http://localhost:5000
```

Health check: `GET http://localhost:5000/health` -> `{"status": "ok"}`

---

## API

Base path: `/api/v1`

### 1. Upload a CSV  (asynchronous)

```
POST /api/v1/uploads
Content-Type: multipart/form-data
form field: file=<your.csv>
```

A 1 GB file takes minutes to ingest, so the request does **not** block on it:
the file is streamed to disk, a job is recorded, and the API returns immediately.

**202 Accepted**
```json
{ "job_id": "a1b2c3...", "status": "PENDING", "status_url": "/api/v1/uploads/a1b2c3..." }
```

### 2. Check upload status

```
GET /api/v1/uploads/<job_id>
```
```json
{
  "job_id": "a1b2c3...",
  "status": "COMPLETED",        // PENDING | PROCESSING | COMPLETED | FAILED
  "processed": 45000,           // rows inserted
  "skipped": 12,                // duplicates skipped
  "failed": 3,                  // rows that couldn't be parsed
  "errors_sample": [ { "row": 1234, "error": "missing title" } ]
}
```

### 3. List movies

```
GET /api/v1/movies
```

| Param      | Type | Default        | Notes                                            |
|------------|------|----------------|--------------------------------------------------|
| `page`     | int  | 1              |                                                  |
| `limit`    | int  | 20 (max 100)   |                                                  |
| `language` | str  | —              | Filters on `original_language`, e.g. `en`, `fr`  |
| `year`     | int  | —              | Year of release                                  |
| `sort`     | str  | `release_date` | `release_date` or `ratings`                      |
| `order`    | str  | `desc`         | `asc` or `desc`                                  |

Example: `/api/v1/movies?language=en&year=1995&sort=ratings&order=desc&page=1&limit=20`

**200 OK**
```json
{
  "data": [ { "id": "...", "title": "Toy Story", "year": 1995, "vote_average": 7.7, "...": "..." } ],
  "pagination": { "page": 1, "limit": 20, "total": 312, "total_pages": 16, "has_next": true, "has_prev": false }
}
```

Errors use a consistent shape: `{ "error": { "code": "BAD_REQUEST", "message": "..." } }`

---

## Testing

```bash
pytest -q
```
Tests use **mongomock**, so they run without a real MongoDB. They cover the
response envelope, language/year filtering, rating sort, pagination, and
validation (a 400 on a disallowed sort field).

A **Postman collection** is included: `postman_collection.json` (import it into
Postman to exercise upload + status + list against a running server).

---

## Design notes

**Project layout** (separation of concerns):
```
app/
  api/            # HTTP layer (blueprints) -- request/response only
  services/       # business logic (query building, CSV ingest)
  repositories/   # the ONLY place that talks to MongoDB
  models/         # CSV row -> clean document transform + validation
  utils/          # response/error helpers
  db.py           # Mongo client + index definitions
config.py         # env-driven config
run.py            # entry point
```

**Handling the 1 GB scale.** A 1 GB CSV is roughly 2.5 million rows. We never
load the file into memory: `csv.DictReader` streams it row by row, rows are
batched, and each batch goes in with one `insert_many`. The upload is processed
in a background thread so the HTTP request returns immediately with a job id.
*Production upgrade path:* move the ingest function to a Celery task (Redis
broker) for horizontal scaling and restart-safety -- the ingest logic is
unchanged, only the trigger differs.

**Data cleaning** (decided from analysing the sample CSV):
- `release_date` (string) -> real date; an integer `year` is **derived** at
  ingest for fast, indexable year filtering. ~0.18% of rows have no date and
  store `null`.
- `languages` (a stringified list like `"['English']"`) is parsed into a real
  array. Its values are dirty (empties, encoding junk), so the **language
  filter uses `original_language`** (clean ISO codes) instead.
- `vote_count` (float in the CSV) is cast to int.

**Indexes** follow the ESR rule (Equality, then Sort): the filtered field leads,
the sort field follows -- e.g. `{original_language: 1, release_date: -1}`. A
unique index on `(title, release_date)` enforces de-duplication on re-upload
(this pair was unique across the whole sample).

**Pagination.** Uses `skip`/`limit` for simplicity. For very deep pages on
millions of rows, keyset (cursor) pagination -- filtering on the last seen sort
value -- scales better, since `skip` must still walk the skipped documents.

**Assumptions.** `title` is required (it has no nulls in the data). `(title,
release_date)` is the natural key since the dataset has no movie id column.
