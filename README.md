# Order Service — FastAPI + Kafka + MySQL + SQLAlchemy

A small but realistic order-management backend used as a **brownfield sample
repo**: an existing, working codebase with normal production patterns
(layered architecture, migrations, async event publishing, a background
worker, and a test suite) that an agent can be pointed at to extend, refactor,
or debug.

## Domain

An e-commerce style order pipeline:

- **Users** place **Orders**.
- Orders contain one or more **Order Items**, each referencing a **Product**.
- Creating or updating an order publishes an event to **Kafka**.
- A separate **worker** process consumes those events and keeps
  `stock_quantity` on each product in sync (decrementing on `order.created`,
  restocking on cancellation), writing an audit trail to `inventory_logs`.

```
                 ┌────────────┐        order.created
   HTTP  ───────▶│  FastAPI   │──────────────┐   order.status_updated
                 │  (app)     │──────────────┼───────────┐
                 └─────┬──────┘              ▼           ▼
                       │                 ┌─────────────────────┐
                       ▼                 │        Kafka         │
                 ┌────────────┐          └──────────┬──────────┘
                 │   MySQL    │                     │
                 │ (SQLAlchemy)◀────────────────────┘
                 └────────────┘   worker consumes events,
                                   updates stock & inventory_logs
```

## Tech stack

| Layer       | Choice                                   |
|-------------|-------------------------------------------|
| API         | FastAPI + Uvicorn                          |
| ORM         | SQLAlchemy 2.0 (declarative, sync)         |
| Database    | MySQL 8 (via PyMySQL driver)               |
| Migrations  | Alembic                                    |
| Messaging   | Kafka (via `kafka-python`)                 |
| Validation  | Pydantic v2                                |
| Tests       | pytest + FastAPI `TestClient` + SQLite     |

## Project layout

```
app/
├── main.py               # FastAPI app + route registration
├── core/                 # settings, DB session, logging
├── models/                # SQLAlchemy ORM models
├── schemas/               # Pydantic request/response models
├── api/v1/                # HTTP routers (users, products, orders)
├── services/               # business logic, called by routers and the worker
├── kafka/                 # event schemas, producer, consumer
└── worker.py               # entrypoint for the standalone Kafka consumer process
migrations/                 # Alembic migration scripts
tests/                       # pytest suite (SQLite + mocked Kafka, no infra needed)
```

## Running it locally with Docker

```bash
cp .env.example .env
docker compose up --build
```

This starts MySQL, Kafka (+ Zookeeper), the FastAPI app (port `8000`), and the
worker process. The app container runs `alembic upgrade head` on startup, so
the schema is created automatically.

- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

### Example requests

```bash
# Create a user
curl -X POST localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{"email":"jane@example.com","full_name":"Jane Doe","password":"supersecret123"}'

# Create a product
curl -X POST localhost:8000/api/v1/products \
  -H "Content-Type: application/json" \
  -d '{"sku":"SKU-001","name":"Wireless Mouse","price":"29.99","stock_quantity":50}'

# Place an order (publishes an `order.created` event)
curl -X POST localhost:8000/api/v1/orders \
  -H "Content-Type: application/json" \
  -d '{"user_id":1,"items":[{"product_id":1,"quantity":2}]}'

# Advance order status (publishes an `order.status_updated` event)
curl -X PATCH localhost:8000/api/v1/orders/1/status \
  -H "Content-Type: application/json" \
  -d '{"status":"confirmed"}'
```

## Running without Docker

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt

# point DATABASE_URL / KAFKA_BOOTSTRAP_SERVERS at your own MySQL/Kafka, then:
alembic upgrade head
uvicorn app.main:app --reload

# in a second terminal, run the event consumer:
python -m app.worker
```

## Tests

The test suite talks to an in-memory SQLite database and a fake in-memory
event publisher, so it runs with **no external services**:

```bash
pytest -v
```

## Environment variables

See `.env.example`. Key ones:

| Variable                          | Purpose                                   |
|------------------------------------|--------------------------------------------|
| `DATABASE_URL`                      | SQLAlchemy connection string for MySQL      |
| `KAFKA_BOOTSTRAP_SERVERS`           | Kafka broker address(es)                    |
| `KAFKA_TOPIC_ORDER_CREATED`         | Topic for new-order events                  |
| `KAFKA_TOPIC_ORDER_STATUS_UPDATED`  | Topic for order status-change events        |
| `KAFKA_CONSUMER_GROUP`              | Consumer group id used by `app/worker.py`   |

## Known limitations (intentionally left as-is)

- **Stock is decremented asynchronously.** The order API only *validates*
  stock at creation time; the actual decrement happens later when the
  worker consumes the `order.created` event. Under concurrent load this
  leaves a small window where two orders could both pass the stock check
  for the last unit of a product. A stricter design would reserve stock
  synchronously inside the request transaction.
- **No authentication/authorization** — endpoints are open. Password
  hashing is implemented (`passlib`/bcrypt) but there's no login/token flow.
- **No pagination metadata** — list endpoints support `skip`/`limit` but
  don't return total counts or next-page links.

These are left in deliberately so there's real, meaningful work available
for an agent to pick up.
