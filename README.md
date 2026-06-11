# de-scheduling-evolution

> One problem. Six tools. The real reason behind every decision.

---

## What Is This?

A data engineer needs to collect data. The collection must be automated, periodic, and reliable.

**Which tool do they use?**

The answer depends on context — company size, team maturity, infrastructure, cost. This project makes those contexts concrete.

The same pipeline is implemented six times, with six different scheduling tools. Each implementation starts where the previous tool falls short. Every decision is explained. Every trade-off is visible.

---

## The Pipeline

Every chapter solves the same problem:

```
Fetch weather data from OpenWeatherMap API
        ↓
Validate with Pydantic
        ↓
Upsert into PostgreSQL
        ↓
Schedule & automate
```

What changes across chapters: **only the scheduling layer.**

---

## The Evolution

| # | Tool | Story | Why We Left |
|---|---|---|---|
| 01 | Cron | I wrote a script, I want it to run automatically | No logging, no retry, silent failures |
| 02 | APScheduler | I want to manage scheduling inside the application | Scheduler dies with the process, no state |
| 03 | Celery Beat | It became distributed, I need a queue | No DAG, no dependency management |
| 04 | Airflow | Dependencies exist, monitoring needed, team grew | Heavy on single server, not container-native |
| 05 | Prefect | Airflow is too heavy, what is the modern alternative? | Weak native Kubernetes integration |
| 06 | Airflow on Kubernetes | Everything runs on K8s, Airflow moves there too | — This is the peak |

---

## Design Principles

**Control variable correctness.**
The data source (API) and destination (PostgreSQL) never change. Only the orchestration layer changes. This is a pure comparison — no noise, no distraction.

**Every tool earns its place.**
No tool is introduced without a concrete reason. Each chapter opens with the previous tool's failure.

**Production standards from day one.**
Even the simplest Cron implementation uses Pydantic for validation, Tenacity for retry, and Structlog for structured logging. The bar does not drop.

**Zero cost.**
Every implementation runs locally or with free, self-hosted tools. Paid alternatives are explained, not implemented.

---

## Each Chapter Contains

```
1. Story context      — Why the previous tool was not enough
2. Implementation     — Setup, code, execution
3. Identity card      — Cost, company type, team size, alternatives
4. Decision guide     — When to use, when not to use
5. Comparison         — What changed from the previous chapter
```

---

## Identity Card Format

Every tool is evaluated on the same axes:

```
Cost          → Zero / Low / Medium / High
Company type  → Solo / Startup / Scale-up / Enterprise
Team size     → Minimum and ideal
Maturity      → Age and adoption
Alternatives  → Free and paid options
```

---

## Technical Foundation

### Shared Layer
All chapters share the same core logic:

```
shared/
├── extractor.py    → fetch_weather(city, target_time=None)
├── loader.py       → PostgreSQL upsert
├── models.py       → Pydantic schemas
└── alembic/        → DB migrations, runs on startup
```

### Key Decisions

**Idempotency**
Unique constraint on `(city, timestamp)`. Duplicate runs do not corrupt data.

**Time management**
`target_time` parameter in every extractor call. Cron passes system time. Airflow passes `{{ ds }}`. Backfill works correctly.

**Isolation**
Each chapter has its own `requirements.txt` and `Dockerfile`. The shared layer is copied into each container. No dependency conflicts between chapters.

---

## Repository Structure

```
de-scheduling-evolution/
├── README.md
├── docker-compose.infra.yml     ← PostgreSQL + Redis
├── shared/
│   ├── __init__.py
│   ├── extractor.py
│   ├── loader.py
│   ├── models.py
│   └── alembic/
├── 01-cron/
├── 02-apscheduler/
├── 03-celery-beat/
├── 04-airflow/
├── 05-prefect/
└── 06-airflow-on-kubernetes/
```

Each directory runs independently. Each has its own README and identity card.

---

## Cost Guarantee

| Tool | Local Solution |
|---|---|
| Cron | OS built-in |
| APScheduler | pip install |
| Celery Beat | pip install + Redis (Docker) |
| Airflow | Docker, self-hosted |
| Prefect | Self-hosted core |
| Airflow on Kubernetes | Minikube + Helm |

---

## Who Is This For?

- A **junior data engineer** who needs to understand why tools exist, not just how to use them.
- A **mid-level DE** making a scheduling decision for a new project.
- A **tech lead** who needs a reference to explain trade-offs to their team.
- Anyone who has ever installed Airflow for a five-minute script.

---

## What This Is Not

- A tutorial on how to use each tool in isolation.
- A benchmark with performance numbers.
- A cloud deployment guide.

---

*Part of the `de-` series — reference-quality, open-source data engineering projects.*
