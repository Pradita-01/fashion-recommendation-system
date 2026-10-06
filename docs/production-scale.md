# Production Scale Considerations

## 1. Current Deployment Model

The current project is a production-oriented local implementation using Docker Compose.

The local architecture contains:

```text
Frontend
Backend
PostgreSQL
Qdrant
Redis
```

This provides a reproducible development and demonstration environment.

The current system is not presented as a fully distributed cloud deployment.

---

# 2. Scaling Objective

The architecture should support growth in:

- catalogue size
- query volume
- concurrent users
- multilingual traffic
- catalogue update frequency
- model inference requirements

Scaling should preserve:

- retrieval quality
- latency
- reliability
- consistency
- observability

---

# 3. API Scaling

FastAPI is suitable for horizontal scaling because the API layer can be deployed as multiple stateless instances.

A production architecture could use:

```text
                    Load Balancer
                         │
             ┌───────────┼───────────┐
             ▼           ▼           ▼
          API #1       API #2       API #3
```

The instances would share external infrastructure such as:

- PostgreSQL
- Qdrant
- Redis
- model-serving infrastructure

---

# 4. Database Scaling

PostgreSQL is the authoritative source for product metadata.

At larger scale, PostgreSQL can be extended using:

- connection pooling
- read replicas
- query optimization
- appropriate indexes
- partitioning where justified
- managed database infrastructure

The key architectural principle is:

```text
PostgreSQL
    =
Authoritative Catalogue
```

---

# 5. Vector Database Scaling

Qdrant contains derived vector representations used for retrieval.

At larger scale, Qdrant can be deployed with:

- replication
- sharding
- distributed nodes
- dedicated resource allocation
- backup and recovery procedures

The vector index should remain rebuildable from the authoritative catalogue.

This reduces the risk of treating the vector store as the only source of truth.

---

# 6. Catalogue Ingestion

An evolving catalogue requires incremental ingestion.

A scalable ingestion pipeline can follow:

```text
                Catalogue Update
                       │
                       ▼
                  Validation
                       │
                       ▼
                  PostgreSQL
                       │
                       ▼
                Change Detection
                       │
                       ▼
              Embedding Generation
                       │
                       ▼
                 Qdrant Update
```

Only new or changed products should be embedded again.

This avoids unnecessary full-catalogue reindexing.

---

# 7. Asynchronous Processing

Catalogue ingestion and embedding generation should be separated from the synchronous search API.

A production system can use background workers:

```text
Catalogue
    ↓
Queue
    ↓
Ingestion Worker
    ↓
Embedding Worker
    ↓
Vector Index
```

This prevents large ingestion jobs from blocking user-facing search traffic.

---

# 8. Embedding Generation

Embedding generation can become expensive as catalogue size increases.

Production optimizations include:

- batch inference
- GPU inference where economically justified
- asynchronous processing
- incremental embeddings
- embedding versioning
- model-specific vector collections

Embedding versions should be tracked so that an index can be rebuilt consistently after model changes.

---

# 9. Model Serving

The current system uses the Gemini API for query understanding.

At production scale, model-related concerns include:

- API latency
- request quotas
- API failures
- retry policy
- rate limiting
- cost monitoring
- timeout handling

The application should avoid making the LLM a hard dependency for every possible operation when a safe fallback exists.

---

# 10. Redis Scaling

Redis is used as a caching layer.

Potential cache entries include:

- parsed queries
- repeated search results
- frequently accessed information

At larger scale, Redis can be deployed using an appropriate managed or clustered configuration.

Cache invalidation should account for catalogue changes.

A catalogue version can be incorporated into cache keys to reduce stale-result risk.

---

# 11. Search Latency

Search latency can be divided into:

```text
Request
  ↓
Query Parsing
  ↓
Embedding
  ↓
Dense Retrieval
  ↓
Sparse Retrieval
  ↓
RRF
  ↓
Ranking
  ↓
Database Resolution
  ↓
Response
```

Each stage should be measured independently.

This allows bottlenecks to be identified rather than optimizing the system blindly.

---

# 12. Reliability

Production deployment should include:

- request timeouts
- dependency timeouts
- controlled retries
- health checks
- readiness checks
- structured error handling
- graceful degradation
- rate limiting
- circuit-breaking where appropriate

Optional services should not become unnecessary single points of failure.

---

# 13. Graceful Degradation

A production search system should continue providing useful results when non-critical dependencies fail.

Examples:

### Redis failure

```text
Redis unavailable
      ↓
Skip cache
      ↓
Continue search
```

### Reranker failure

```text
Reranker unavailable
      ↓
Use hybrid ranking
```

### LLM dependency issue

The system should provide an appropriate fallback or controlled error depending on the query requirements.

The objective is to avoid cascading failures across the entire search stack.

---

# 14. Observability

A production deployment should collect structured metrics for:

## API

- request count
- error rate
- latency
- status codes

## Query Understanding

- LLM request count
- LLM latency
- parser failures
- fallback rate

## Retrieval

- dense retrieval latency
- sparse retrieval latency
- fusion latency
- ranking latency
- candidate counts

## Cache

- cache hits
- cache misses
- cache latency

## Infrastructure

- CPU
- memory
- storage
- database connections
- Qdrant resource usage

## Quality

- nDCG
- Recall
- MRR
- user feedback
- language-level performance

---

# 15. Evaluation in Production

Offline evaluation should be complemented by continuous evaluation.

A production-quality evaluation loop could be:

```text
Golden Evaluation
       ↓
CI Evaluation
       ↓
Deployment
       ↓
Production Feedback
       ↓
New Evaluation Data
       ↓
Updated Golden Set
```

This allows retrieval quality to be monitored as the catalogue, query distribution, and models change.

---

# 16. Security

A production deployment should include:

- secret management
- API authentication where required
- HTTPS
- rate limiting
- input validation
- dependency scanning
- container image scanning
- restricted database access
- restricted vector-store access

API keys should never be stored in source control.

---

# 17. Deployment Evolution

The current Docker Compose environment can evolve toward:

```text
Local Development
       ↓
Containerized Deployment
       ↓
Managed Infrastructure
       ↓
Horizontal API Scaling
       ↓
Distributed Retrieval
       ↓
Automated CI/CD
       ↓
Continuous Evaluation
```

A future production environment could use:

- managed PostgreSQL
- managed Redis
- distributed Qdrant
- container orchestration
- centralized logging
- monitoring
- alerting
- automated deployments

---

# 18. Catalogue Consistency

The authoritative data model should remain:

```text
PostgreSQL
     │
     ├── Product Metadata
     ├── Catalogue Version
     └── Product State
```

while:

```text
Qdrant
     │
     └── Derived Embeddings / Retrieval Index
```

When catalogue data changes, the system should update the derived retrieval representation accordingly.

Catalogue versions can help coordinate:

- ingestion
- indexing
- cache invalidation
- rollback
- evaluation

---

# 19. Cost Considerations

Production scaling should balance quality and cost.

Potential cost drivers include:

- Gemini API calls
- embedding generation
- GPU infrastructure
- vector storage
- database storage
- Redis
- network traffic
- observability infrastructure

Caching and batching can reduce unnecessary model calls.

The reranker experiment also demonstrates why expensive additional inference should only be enabled when it produces measurable quality improvements.

---

# 20. Scaling Strategy

A practical scaling strategy is:

### Stage 1 — Current

```text
Docker Compose
20,000 products
Single PostgreSQL
Single Qdrant
Single Redis
```

### Stage 2 — Growing Catalogue

```text
Incremental ingestion
Batch embeddings
Improved indexing
Redis caching
API horizontal scaling
```

### Stage 3 — Production

```text
Load Balancer
Multiple API instances
Managed PostgreSQL
Distributed Qdrant
Managed Redis
Background workers
Centralized observability
```

### Stage 4 — Large Scale

```text
Distributed ingestion
Dedicated model serving
Autoscaling
Continuous evaluation
Advanced ranking
Online feedback loops
```

---

# 21. Current Limitations

The current implementation does not claim to be a fully distributed production deployment.

The following are architectural considerations rather than implemented infrastructure:

- Kubernetes
- distributed Qdrant
- PostgreSQL read replicas
- managed Redis
- dedicated model-serving cluster
- centralized production observability
- autoscaling
- production load balancing

These can be added as deployment scale increases.

---

# 22. Production Readiness Principles

The main production principles are:

### Reliability

Dependencies should fail gracefully.

### Scalability

Stateless API services should be horizontally scalable.

### Reproducibility

Docker provides a consistent application environment.

### Measurability

Every major retrieval decision should be measurable.

### Replaceability

Models and retrieval components should be independently replaceable.

### Data Authority

PostgreSQL remains the authoritative product catalogue.

### Derived Indexes

Vector indexes should be rebuildable.

### Evaluation-Driven Development

Changes to ranking or retrieval should be validated using evaluation data.

---

# 23. Summary

The current system provides a strong foundation for production scaling.

The most important architectural distinction is:

```text
Authoritative Data
       ↓
PostgreSQL

Derived Retrieval Representation
       ↓
Qdrant

Fast Repeated Access
       ↓
Redis

User-Facing API
       ↓
FastAPI

User Interface
       ↓
React + Nginx
```

The architecture can therefore evolve from a reproducible local Docker Compose deployment into a horizontally scaled production system without changing the fundamental responsibilities of the major components.
