# Additional Exploration

## 1. Purpose

The project includes additional experiments beyond the primary hybrid retrieval implementation.

The purpose of these experiments is to understand:

- whether dense retrieval is sufficient
- whether sparse retrieval provides complementary value
- whether hybrid retrieval improves measured quality
- whether reranking improves the hybrid result
- how retrieval behaves across languages

The experiments are evaluated using the same golden evaluation methodology.

---

# 2. Dense Retrieval Exploration

The first retrieval configuration uses BGE-M3 embeddings with Qdrant.

```text
Query
  ↓
BGE-M3
  ↓
Qdrant
  ↓
Dense Results
```

Measured performance:

| Metric | Score |
|---|---:|
| nDCG@10 | 0.7530 |
| Recall@10 | 0.4275 |
| MRR | 0.8356 |

Dense retrieval provides semantic matching and multilingual representation.

However, semantic similarity alone does not guarantee strong lexical matching for every fashion query.

---

# 3. Sparse Retrieval Exploration

The second configuration uses BM25.

```text
Query
  ↓
BM25
  ↓
Sparse Results
```

Measured performance:

| Metric | Score |
|---|---:|
| nDCG@10 | 0.7000 |
| Recall@10 | 0.3587 |
| MRR | 0.7267 |

BM25 provides useful lexical matching.

It is particularly useful for product terminology and exact words, but does not provide the same semantic representation as dense retrieval.

---

# 4. Hybrid Retrieval Exploration

The third configuration combines dense and sparse retrieval.

```text
             ┌── Dense BGE-M3 ──┐
Query ───────┤                  ├── RRF ──→ Results
             └── Sparse BM25 ───┘
```

Reciprocal Rank Fusion is used to combine the rankings.

Measured performance:

| Metric | Score |
|---|---:|
| nDCG@10 | **0.9010** |
| Recall@10 | **0.8378** |
| MRR | **0.9500** |

The hybrid configuration achieved the strongest measured retrieval performance among the evaluated configurations.

---

# 5. Reranker Exploration

A BGE reranker was evaluated as an additional ranking stage.

The experimental pipeline was:

```text
Query
  ↓
Dense + Sparse Retrieval
  ↓
RRF
  ↓
BGE Reranker
  ↓
Final Results
```

Measured results:

| Configuration | nDCG@10 | Recall@10 | MRR |
|---|---:|---:|---:|
| Hybrid | **0.9010** | **0.8378** | **0.9500** |
| Hybrid + Reranker | 0.8532 | 0.6463 | 0.9250 |

The reranker did not improve the measured retrieval metrics.

Therefore it was not enabled in the production search path.

This is an important engineering decision because adding another neural ranking stage introduces additional:

- inference cost
- latency
- memory requirements
- operational complexity

without demonstrated quality improvement in this evaluation.

---

# 6. Why the Reranker Was Kept as an Experimental Component

The reranker implementation remains in the repository because it represents a meaningful retrieval experiment.

Keeping the implementation allows future experimentation with:

- different candidate sizes
- different reranker models
- model-specific tuning
- language-specific evaluation
- alternative ranking strategies

However, the production path uses the empirically stronger hybrid configuration.

---

# 7. Multilingual Exploration

The project also explores multilingual search.

The embedding layer uses BGE-M3.

The current evaluation includes:

```text
English
Tamil
Hindi
```

Measured language-level results:

| Language | Queries | nDCG@10 | Recall@10 | MRR |
|---|---:|---:|---:|---:|
| English | 17 | 0.9433 | 0.8680 | 1.0000 |
| Tamil | 2 | 0.4914 | 0.5000 | 0.5000 |
| Hindi | 1 | 1.0000 | 1.0000 | 1.0000 |

The results show why multilingual evaluation must be considered separately.

The Tamil and Hindi subsets are too small to support broad conclusions, so expanding the multilingual golden set is an important future improvement.

---

# 8. Query Understanding Exploration

The project separates LLM-based query understanding from product retrieval.

Example:

```text
User:
"lightweight comfortable clothes for summer"

        ↓

Gemini

        ↓

Intent:
Search

Category:
Clothing

Season:
Summer

Attributes:
Lightweight
Comfortable

Language:
English

Normalized Query:
"lightweight comfortable clothes for summer"
```

This design allows the system to inspect how the LLM interpreted the request while keeping the actual product retrieval measurable.

---

# 9. Why the LLM Does Not Select Products

A key architectural decision is that Gemini is not treated as the final recommendation engine.

Instead:

```text
Gemini
   =
Query Understanding

Retrieval
   =
Candidate Discovery

Ranking
   =
Ordering Candidates
```

This separation provides several benefits:

- retrieval can be evaluated independently
- ranking can be compared experimentally
- model hallucination is less likely to directly determine product selection
- retrieval quality can be measured using relevance labels
- components can be independently replaced

---

# 10. Experimentation Principle

The project follows an evaluation-driven approach:

```text
Hypothesis
    ↓
Implementation
    ↓
Evaluation
    ↓
Comparison
    ↓
Engineering Decision
```

For example:

```text
Hypothesis:
Reranking may improve hybrid retrieval.

        ↓

Experiment:
Hybrid + BGE Reranker.

        ↓

Measured Result:
Performance decreased.

        ↓

Decision:
Do not enable reranking in production.
```

This avoids increasing architecture complexity without measurable benefit.

---

# 11. Additional Areas for Exploration

Future experiments can investigate:

### Embedding Models

Compare additional multilingual embedding models against BGE-M3.

### Fusion Methods

Compare RRF against learned or score-based fusion.

### Query Expansion

Evaluate whether query expansion improves recall.

### Catalogue Growth

Measure retrieval quality as catalogue size increases.

### Language Expansion

Expand evaluation beyond English, Tamil, and Hindi.

### Feedback Learning

Use user interactions to improve ranking.

### Explanation Quality

Measure whether generated explanations are supported by retrieved product attributes.

---

# 12. Key Findings

The main experimental findings are:

1. Dense retrieval provides strong semantic retrieval capability.
2. Sparse retrieval provides complementary lexical matching.
3. Hybrid retrieval achieved the strongest measured retrieval performance.
4. The tested reranker degraded the measured evaluation scores.
5. Multilingual performance varies by language and requires language-specific evaluation.
6. The LLM is most useful as a query-understanding component rather than as an opaque product selector.
7. Evaluation should drive architectural complexity.

---

# 13. Conclusion

The exploration demonstrates that the system architecture was not selected solely because individual technologies are popular.

Instead, major retrieval decisions were validated through experiments.

The resulting production path is:

```text
Gemini Query Understanding
          ↓
BGE-M3
          ↓
Dense + BM25
          ↓
RRF
          ↓
Lightweight Ranking
          ↓
Products
```

while alternative approaches remain available for future experimentation.
