# Fashion Recommendation & Semantic Search System

> A production-oriented multilingual fashion discovery system that converts natural-language requests into structured intent and combines dense semantic retrieval with sparse lexical retrieval to produce relevant, explainable product recommendations.

---

## 1. Overview

Fashion search is often expressed in natural language rather than structured filters.

A user may search for:

- `lightweight comfortable clothes for summer`
- `office wear for women`
- `गर्मियों के लिए हल्के और आरामदायक कपड़े`
- `கோடைக்கு வசதியான லைட் வெயிட் ஆடைகள்`

Traditional keyword search can struggle with multilingual queries, implicit preferences, semantic similarity, and evolving product catalogues.

This project addresses that problem through a **multilingual semantic fashion recommendation and search pipeline** combining:

- Gemini-based query understanding
- Structured intent extraction
- BGE-M3 multilingual embeddings
- Dense vector retrieval
- Sparse BM25 retrieval
- Reciprocal Rank Fusion (RRF)
- PostgreSQL product metadata
- Redis caching
- Qdrant vector search
- Lightweight ranking
- Grounded recommendation explanations
- Retrieval evaluation and ablation experiments
- Dockerized execution

The system is designed as a **measurable retrieval system**, rather than treating the LLM itself as the product-ranking mechanism.

---

# 2. Problem Statement

Build a fashion discovery system that can understand multilingual natural-language requests, retrieve semantically relevant products from an evolving catalogue, and provide measurable evidence of retrieval quality.

The system should:

1. Understand natural-language fashion requests.
2. Extract structured intent and attributes.
3. Support multilingual queries.
4. Retrieve products using semantic and lexical signals.
5. Combine dense and sparse retrieval.
6. Rank results using measurable retrieval logic.
7. Provide grounded explanations for recommendations.
8. Support evaluation through a manually reviewed golden set.
9. Provide reproducible local execution.
10. Have a clear path toward production-scale deployment.

---

# 3. Key Features

## Natural-Language Query Understanding

Gemini converts a user query into a structured representation containing information such as:

- intent
- category
- occasion
- season
- attributes
- language
- normalized query

Example:

```text
User query:
"lightweight comfortable clothes for summer"

Parsed intent:
- Intent: Search
- Category: Clothing
- Season: Summer
- Attributes: Lightweight, Comfortable
- Language: English

'''
## Multi lingual approach:


