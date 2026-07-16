# Real-Time Formula 1 Analytics Platform

**Streaming pipeline** — OpenF1 → Kafka → Spark (Bronze/Silver/Gold) → DuckDB → FastAPI → React Dashboard

Ingests live Formula 1 race data through a medallion architecture and serves real-time analytics via interactive dashboards with AI-generated race summaries.

**Source repo:** [lionaelsurya/f1-analytics-platform](https://github.com/lionaelsurya/f1-analytics-platform)

## Architecture

```
OpenF1 API → Python Producer → Kafka → Spark Structured Streaming
                                        ↓
                                   Delta Lake
                                ┌──────┼──────┐
                             Bronze Silver  Gold
                                             ↓
                                        DuckDB → FastAPI → React Dashboard
                                                         → AI Service
```

## Stack

| Component | Technology |
|-----------|-----------|
| Ingestion | Python (httpx, aiokafka) |
| Event Bus | Apache Kafka 7.6 |
| Processing | Spark Structured Streaming 3.5 |
| Storage | Delta Lake 3.1 |
| Analytics | DuckDB 1.1 |
| API | FastAPI 0.109 |
| Frontend | React 18, TypeScript 5.3, Recharts |
| AI | OpenAI / Anthropic (provider-agnostic) |
| Container | Docker Compose |
| CI | GitHub Actions |

## Key Differentiators

- **Repository → Service → Controller** pattern in the API layer
- All SQL isolated in Repository layer (no inline queries in services or controllers)
- AI layer grounded in Gold analytical data only — no raw event access
- Type-safe across the stack (Python type hints, Pydantic, TypeScript strict)
- 48 passing tests (31 unit + 17 integration contract tests)

## Links

- [Source Repository](https://github.com/lionaelsurya/f1-analytics-platform)
- [Architecture Docs](https://github.com/lionaelsurya/f1-analytics-platform/tree/main/docs)
- [API Reference](https://github.com/lionaelsurya/f1-analytics-platform#api-endpoints)

---

Back to [Data Engineering](../README.md) or [main portfolio](../../README.md).
