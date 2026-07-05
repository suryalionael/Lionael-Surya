# Streaming Clickstream Pipeline

Real-time streaming analytics for e-commerce clickstream data — Kafka, Spark Structured Streaming, Delta Lake, DuckDB, and Streamlit.

[![GitHub](https://img.shields.io/badge/Source-GitHub-181717?logo=github)](https://github.com/suryalionael/streaming-clickstream-pipeline)
[![License](https://img.shields.io/badge/License-MIT-yellow)](https://github.com/suryalionael/streaming-clickstream-pipeline/blob/main/LICENSE)

## Project Status

| Area | Status |
|---|---|
| Synthetic event generator | Done |
| Kafka ingestion + dead-letter queue | Done |
| Spark streaming (Bronze → Silver → Gold) | Done |
| Delta Lake medallion architecture | Done |
| DuckDB analytics layer | Done |
| Streamlit dashboard (6 pages) | Done |
| Docker Compose orchestration | Done |
| CI/CD (GitHub Actions) | Done |
| Test suite (74 tests) | Done |
| Code quality (Ruff, Black, isort, mypy — 0 errors) | Done |

## Business Problem

E-commerce platforms generate a continuous stream of clickstream events: page views, searches, product interactions, cart actions, and purchases. To understand user behavior, conversion funnels, and product performance in real time, these events must be ingested, processed, and analyzed with minimal latency.

This pipeline solves that problem by:
- Ingesting ~50 events/second from a synthetic clickstream generator into Kafka
- Processing with Spark Structured Streaming at 10-second micro-batch intervals
- Persisting as a Delta Lake medallion (Bronze → Silver → Gold) on MinIO
- Serving live analytics via DuckDB and a Streamlit dashboard

## Architecture

### Data Flow

```
Synthetic Generator ──▶ Kafka ──▶ Spark Streaming ──▶ Delta Lake ──▶ DuckDB ──▶ Dashboard
                              │                         │
                              ▼                         ▼
                         Dead Letter               Bronze → Silver → Gold
                         (invalid events)           (medallion layers)
```

### Medallion Layers

| Layer | Description | Key Transforms |
|---|---|---|
| **Bronze** | Raw events + ingestion metadata | JSON parsing, schema enforcement, partition columns |
| **Silver** | Cleaned, validated, deduplicated | Time range filtering, validation, enrichment, dedup, session flags |
| **Gold** | Aggregated business metrics | Funnel conversion, product performance, traffic analytics |

### Streaming Guarantees

- **Exactly-once semantics**: `foreachBatch` with idempotent Delta writes + Kafka offset tracking
- **Out-of-order handling**: 10-minute watermark delay for late-arriving events
- **Fault tolerance**: Checkpointing, graceful shutdown, consumer group rebalancing
- **Dead letter queue**: Unparseable Kafka messages preserved with failure metadata

## Quick Start

```bash
git clone https://github.com/suryalionael/streaming-clickstream-pipeline.git
cd streaming-clickstream-pipeline
docker compose up -d
```

Then access:
- **Dashboard**: http://localhost:8501
- **Kafka UI**: http://localhost:8080
- **MinIO Console**: http://localhost:9001 (`minioadmin`/`minioadmin`)

## Tech Stack

| Component | Technology | Role |
|---|---|---|
| Event broker | Apache Kafka 7.6 | Durable, partitioned event log (6 partitions) |
| Stream processing | Spark Structured Streaming 3.5 | Event-time processing, watermarking, micro-batches |
| Storage layer | Delta Lake 3.2 on MinIO | ACID transactions, schema evolution, time travel |
| Analytics | DuckDB | Embedded OLAP, zero-config, reads Delta/Parquet |
| Dashboard | Streamlit | 6-page real-time analytics UI |
| Orchestration | Docker Compose | 7-service stack with health checks |

## Services

| Service | Port | Purpose |
|---|---|---|
| Producer | — | Synthetic event generator (~50 ev/s) |
| Kafka | 9092 | Message broker |
| Kafka UI | 8080 | Cluster management |
| Spark | 4040 | Streaming pipeline |
| MinIO API | 9000 | S3-compatible object storage |
| MinIO Console | 9001 | Storage management UI |
| Dashboard | 8501 | Real-time analytics |

## Testing

| Suite | Tests | Scope |
|---|---|---|
| Unit | 44 | State machine, validation, serialization |
| Edge case | 18 | Malformed JSON, nulls, duplicates, schema evolution |
| Spark integration | 6 | Silver/Gold transforms |
| Docker smoke | 6 | Service health, end-to-end pipeline |

## Dashboard Pages

1. **Overview** — KPI cards with sparklines and trend arrows
2. **Traffic** — Time-series traffic charts
3. **Funnel** — Conversion funnel visualization
4. **Geography** — Geographic event distribution
5. **Products** — Product performance table
6. **Infrastructure** — Pipeline health monitoring (row counts, freshness, EPS, dead-letter count, HTTP checks)

## Design Decisions

| Decision | Rationale |
|---|---|
| Single `foreachBatch` for all 3 layers | Simpler checkpoint management; layers share the same cadence |
| Delta Lake over raw Parquet | Schema evolution and ACID without a separate warehouse |
| DuckDB over full warehouse | Zero-config, lightweight; trade-off is no multi-user concurrency |
| MinIO over cloud S3 | Reproducible local dev; one config change to swap to AWS/GCP |
| Streamlit over Power BI/Tableau | Python-native, rapid iteration, same language as the pipeline |

## Future Improvements

- Authentication and TLS for all services
- Kubernetes deployment with resource limits
- Prometheus metrics and Grafana dashboards
- Delta Lake maintenance jobs (VACUUM, OPTIMIZE)
- Schema registry integration
- Rate limiting with backpressure
- End-to-end data quality monitoring

---

Back to [Data Engineering](../README.md) · [main portfolio](../../README.md) · [Source repo](https://github.com/suryalionael/streaming-clickstream-pipeline)
