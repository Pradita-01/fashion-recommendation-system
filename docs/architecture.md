# System Architecture

## 1. Architecture Overview

The Fashion Recommendation & Semantic Search System is designed as a modular retrieval architecture.

The system separates:

1. User interaction
2. Natural-language query understanding
3. Semantic representation
4. Dense retrieval
5. Sparse retrieval
6. Result fusion
7. Ranking
8. Product metadata resolution
9. Explanation
10. Evaluation

This separation allows individual components to be evaluated, replaced, or scaled independently.

---

## 2. High-Level Architecture
flowchart TB

   

```text
                         ┌──────────────────────┐
                         │        USER          │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ React + TypeScript   │
                         │      Frontend        │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │        Nginx         │
                         │    Reverse Proxy     │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │     FastAPI API      │
                         └──────────┬───────────┘
                                    │
                     ┌──────────────┴──────────────┐
                     │                             │
                     ▼                             ▼
             ┌───────────────┐             ┌─────────────┐
             │ Gemini Parser │             │    Redis    │
             │ Query Intent  │             │    Cache    │
             └───────┬───────┘             └─────────────┘
                     │
                     ▼
              Structured Query
                     │
                     ▼
               BGE-M3 Embedding
                     │
              ┌──────┴──────┐
              │             │
              ▼             ▼
       Dense Retrieval   Sparse Retrieval
          Qdrant              BM25
              │             │
              └──────┬──────┘
                     ▼
          Reciprocal Rank Fusion
                     │
                     ▼
             Lightweight Ranker
                     │
                     ▼
               Product Results
                     │
              ┌──────┴──────┐
              ▼             ▼
        PostgreSQL      Explanation
       Product Data       Layer
```

---

## 3. Frontend Layer

The frontend is implemented using:

- React
- TypeScript
- Vite
- Tailwind CSS

The frontend provides:

- Search interface
- Product browsing
- Parsed intent display
- Product result cards
- Recommendation interaction

The frontend communicates with the backend through the Nginx reverse proxy.

---

## 4. Reverse Proxy

Nginx serves the compiled frontend and proxies API requests to the FastAPI backend.

The browser therefore communicates through:

```text
Browser
   │
   ▼
Nginx
   │
   ├── Frontend assets
   │
   └── /api/*
          │
          ▼
       FastAPI
```

This avoids requiring the browser to communicate directly with the internal Docker service name.

---

## 5. API Layer

The backend is implemented using FastAPI.

Responsibilities include:

- health checks
- query parsing
- product search
- recommendation requests
- API validation
- orchestration of retrieval components

The API exposes versioned search functionality under:

```text
/v1/search
```

---

## 6. Query Understanding

Natural-language queries are passed to the Gemini-based query understanding layer.

The parser extracts structured information such as:

- intent
- category
- occasion
- season
- attributes
- language
- normalized query

Example:

```text
User Query
    ↓
Gemini
    ↓
ParsedQuery
```

The LLM is responsible for understanding the request.

It does not directly determine which products should be returned.

---

## 7. Semantic Representation

The normalized query is converted into an embedding using BGE-M3.

```text
Normalized Query
       │
       ▼
    BGE-M3
       │
       ▼
Dense Vector
```

BGE-M3 provides multilingual semantic representations suitable for the project's multilingual search requirements.

---

## 8. Dense Retrieval

Dense retrieval uses Qdrant as the vector database.

The query vector is compared against indexed product vectors.

```text
Query Vector
     │
     ▼
  Qdrant
     │
     ▼
Dense Candidates
```

The Qdrant index is treated as a derived representation of the authoritative product catalogue.

---

## 9. Sparse Retrieval

Sparse retrieval uses BM25.

BM25 provides lexical matching and is particularly useful for:

- exact terminology
- product vocabulary
- specific words and phrases
- lexical overlap

```text
Query
  │
  ▼
BM25
  │
  ▼
Sparse Candidates
```

---

## 10. Hybrid Retrieval

Dense and sparse retrieval are combined using Reciprocal Rank Fusion.

```text
Dense Candidates ─────┐
                      │
                      ▼
                     RRF
                      ▲
                      │
Sparse Candidates ────┘
```

The purpose of RRF is to combine ranking signals from different retrieval systems without requiring their raw scores to be directly comparable.

---

## 11. Ranking

After hybrid retrieval, the candidate set is processed by the lightweight ranking layer.

The dedicated BGE reranker was evaluated experimentally but is not enabled in the production search path because its measured evaluation performance was lower than the hybrid baseline.

---

## 12. PostgreSQL

PostgreSQL stores authoritative product metadata.

The database contains catalogue information used to resolve and serve product information after retrieval.

The architectural principle is:

```text
PostgreSQL
    =
Authoritative Catalogue
```

while:

```text
Qdrant
    =
Derived Retrieval Index
```

This separation makes the vector index rebuildable from the authoritative catalogue.

---

## 13. Redis

Redis provides caching capabilities.

Potential cacheable operations include:

- repeated search requests
- parsed query results
- frequently accessed information

Caching reduces unnecessary repeated computation and external API calls.

---

## 14. Explanation Layer

The system contains an explanation layer for generating recommendation explanations from retrieved product information.

The explanation layer is kept separate from the retrieval decision path.

This allows retrieval quality to remain independently measurable.

---

## 15. Data Flow

The complete online request flow is:

```text
1. User enters natural-language query
                ↓
2. FastAPI receives request
                ↓
3. Gemini interprets query
                ↓
4. Structured ParsedQuery generated
                ↓
5. Normalized query generated
                ↓
6. BGE-M3 generates embedding
                ↓
7. Dense retrieval through Qdrant
                ↓
8. Sparse retrieval through BM25
                ↓
9. Reciprocal Rank Fusion
                ↓
10. Lightweight ranking
                ↓
11. Product metadata resolution
                ↓
12. Explanation generation
                ↓
13. Results returned to frontend
```

---

## 16. Infrastructure

The local Docker Compose environment contains:

```text
┌─────────────────────────────────────┐
│          Docker Compose             │
│                                     │
│  ┌────────────┐   ┌─────────────┐  │
│  │  Frontend  │   │   Backend   │  │
│  └────────────┘   └──────┬──────┘  │
│                           │         │
│       ┌───────────────────┼──────┐  │
│       │                   │      │  │
│       ▼                   ▼      ▼  │
│  PostgreSQL            Qdrant Redis │
│                                     │
└─────────────────────────────────────┘
```

---

## 17. Design Principles

The architecture follows several principles:

### Separation of Responsibilities

The LLM interprets the query.

Retrieval finds candidates.

Ranking orders candidates.

The database provides authoritative metadata.

The frontend presents results.

### Measurability

Retrieval components can be compared independently.

### Replaceability

Components such as the embedding model, vector store, or ranking layer can be replaced without redesigning the entire system.

### Reproducibility

Docker Compose provides a reproducible local infrastructure layer.

### Evaluation-Driven Complexity

Additional models are introduced only when evaluation demonstrates measurable value.

---

## 18. Architectural Summary

The system can be summarized as:

```text
Natural Language
       ↓
Gemini Query Understanding
       ↓
Structured Intent
       ↓
BGE-M3
       ↓
Dense + Sparse Retrieval
       ↓
RRF
       ↓
Ranking
       ↓
Products
       ↓
Grounded Explanation
```

This architecture provides a modular foundation for multilingual fashion search while keeping retrieval quality measurable and the catalogue authoritative.
