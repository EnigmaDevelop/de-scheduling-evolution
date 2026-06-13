# de-scheduling-evolution

> One problem. Six tools. The real architectural reason behind every scheduling decision.

---

## What Is This?

A data engineer needs to collect data. The collection must be automated, periodic, and reliable.

**Which tool do they use?**

The answer depends entirely on context — company size, team maturity, infrastructure bounds, and cost profiles. This project makes those contexts concrete.

The same ingestion pipeline is implemented six times across six different scheduling layers. Each implementation starts exactly where the previous tool hits its architectural limit. Every decision is explained. Every trade-off is measurable.

---

## The Ingestion Contract

Every chapter solves the exact same data transfer problem:

Fetch weather data from OpenWeatherMap API  
↓  
Validate constraints via Pydantic v2  
↓  
Commit via SQLAlchemy 2.0 ORM (Programmatic Alembic Migrations)  
↓  
Upsert into PostgreSQL (Storing mapped fields + Raw JSONB buffer layer)  
↓  
Automate & Schedule  

What changes across chapters: **only the automation and scheduling layer.**

---

## The Evolution Matrix

| #   | Tool                | Level                  | Architectural Identity                                                                                                        | Why We Left                                                                                                                    |
|-----|---------------------|------------------------|-------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------|
| **01** | **Cron**         | Junior DE / Single Node | Built-in OS automation, zero infrastructure overhead. Container acts as PID 1 boundary.                                      | **OS-level shell isolation, zero native observability dashboards, task overlapping under volume (no backpressure control).**  |
| **02** | **APScheduler**  | In-app Threading       | Gömülü Python scheduling ecosystem, process-level lifecycle control.                                                          | *Pending execution analysis...*                                                                                                 |
| **03** | **Celery Beat**  | Distributed Workers    | Task queue decoupling, asynchronous horizontal scale.                                                                         | *Pending execution analysis...*                                                                                                 |
| **04** | **Airflow**      | Enterprise Orchestration | Heavy-weight central DAG dependency management and logging.                                                                  | *Pending execution analysis...*                                                                                                 |
| **05** | **Prefect**      | Modern Orchestration   | Code-first dynamic tasks, low-boilerplate modern deployment hooks.                                                            | *Pending execution analysis...*                                                                                                 |
| **06** | **Airflow on K8s** | Cloud-Native Peak     | Container-native task-isolation pods. True enterprise production standard.                                                    | — **The Architectural Ceiling**                                                                                                |

---

## Design Principles

- **Control Variable Correctness:** The data source (API JSON layout) and target destination (PostgreSQL 16 Engine) never change. Only the orchestration boundary shifts. This isolates noise and creates a pure comparison framework.
- **Every Tool Earns Its Place:** No tool is introduced as a default choice. Each chapter opens directly by breaking or throttling the previous layer's capacity.
- **Production Standards from Day One:** Even the simplest Cron implementation enforces strict Pydantic parsing, Tenacity exponential backoff retries, unified Structlog structured JSON logs, and programmatic Alembic database state updates on container startup.
- **Zero Cost Isolation:** Every tool runs completely locally or using free, self-hosted container images. Paid alternatives are technically evaluated but never implemented.

---

## Technical Foundation: The Shared Layer

All standalone containers copy and reference the identical business layer directly to prevent code drift between chapters:

```text
shared/
├── alembic/      → Schema versioning scripts tracking engine states (e.g., unique_city_timestamp)
├── alembic.ini   → Local and container configuration mapper
├── extractor.py  → Low-level HTTP requests using Tenacity and structured logging
├── loader.py     → SQLAlchemy ORM declaration, connection factory, and PostgreSQL transactional upserts
└── models.py     → Strict Pydantic parsing schemas isolating raw buffers and parsed items
```

### Key Architectural Decisions

- **Idempotency Contract:** Regulated via a database-level `UniqueConstraint('city', 'timestamp')`. Duplicate runs or backward backfills overwrite mutations safely without state corruption.
- **The Raw JSON Buffer Layer:** To survive upstream API schema evolution, the pipeline saves the complete, raw API response inside a `JSONB` column during the upsert phase. This allows full historical reprocessing if downstream schema fields change retrospectively.
- **Platform Isolation:** Each chapter directory operates independently, carrying its own explicit `requirements.txt`, `Dockerfile`, and local `docker-compose.yaml` linked externally to our shared infrastructure network boundary.

---

## Repository Directory Blueprint

```text
de-scheduling-evolution/
├── README.md
├── docker-compose.infra.yml      ← Common Infrastructure: PostgreSQL 16 + Redis 7 + pgAdmin
├── shared/                       ← The immutable core layer copied during image compilation
│   ├── alembic/
│   ├── extractor.py
│   ├── loader.py
│   └── models.py
├── 01-cron/                      
├── 02-apscheduler/               
├── 03-celery-beat/
├── 04-airflow/
├── 05-prefect/
└── 06-airflow-on-kubernetes/
```

---

## Common Infrastructure Isolation

To guarantee resource optimization, the repository isolates data storage blocks from active compute layers. Run the primary infra layout once from the root directory:

```bash
docker-compose -f docker-compose.infra.yml up -d
```

---

## Who Is This For?

- A **Junior Data Engineer** who needs to understand why enterprise tools exist, rather than just learning syntax.
- A **Mid-level DE** tasked with choosing a scheduling architecture for a greenfield project.
- A **Tech Lead** who needs a clear, reference-grade comparison to explain architectural trade-offs to stakeholders.

---

## What This Is Not

- A basic tutorial on how to install tools in isolation.
- A benchmark tracking raw performance numbers.
- A vendor-driven cloud platform deployment manual.

---

*Part of the `de-` series — reference-quality, open-source data engineering blueprints.*