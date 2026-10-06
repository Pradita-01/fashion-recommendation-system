# Evaluation

## 1. Evaluation Objective

The evaluation framework measures the quality of the fashion retrieval system using a manually reviewed golden subset.

The objective is to determine:

- how well relevant products are retrieved
- how highly relevant products are ranked
- whether hybrid retrieval improves the measured results
- whether reranking provides measurable benefit
- how retrieval behaves across languages

The evaluation is designed to support engineering decisions rather than simply reporting a single overall score.

---

# 2. Evaluation Dataset

The evaluation uses a manually reviewed golden subset.

The golden evaluation contains fashion queries with manually reviewed candidate relevance labels.

The evaluation process includes:

```text
Query
  ↓
Candidate Products
  ↓
Manual Relevance Labels
  ↓
Retrieval Evaluation
  ↓
Metrics
```

The manual review component provides a reference set against which different retrieval configurations can be compared.

---

# 3. Metrics

## nDCG@10

Normalized Discounted Cumulative Gain measures ranking quality while giving greater importance to highly relevant results appearing near the top.

Higher is better.

---

## Recall@10

Recall@10 measures how many of the relevant products are retrieved within the top 10 results.

Higher is better.

---

## MRR

Mean Reciprocal Rank measures how highly the first relevant result appears.

Higher is better.

---

# 4. Retrieval Ablation

The system was evaluated using four retrieval configurations.

| Pipeline | nDCG@10 | Recall@10 | MRR |
|---|---:|---:|---:|
| Dense BGE-M3 | 0.7530 | 0.4275 | 0.8356 |
| Sparse BM25 | 0.7000 | 0.3587 | 0.7267 |
| **Hybrid + RRF** | **0.9010** | **0.8378** | **0.9500** |
| Hybrid + BGE Reranker | 0.8532 | 0.6463 | 0.9250 |

---

# 5. Dense Retrieval

The dense configuration uses:

```text
BGE-M3
   ↓
Qdrant
   ↓
Dense Results
```

Measured:

```text
nDCG@10   = 0.7530
Recall@10 = 0.4275
MRR       = 0.8356
```

Dense retrieval provides semantic matching and multilingual representation.

---

# 6. Sparse Retrieval

The sparse configuration uses BM25.

Measured:

```text
nDCG@10   = 0.7000
Recall@10 = 0.3587
MRR       = 0.7267
```

Sparse retrieval provides lexical matching and complements semantic retrieval.

---

# 7. Hybrid Retrieval

The hybrid pipeline combines:

```text
Dense BGE-M3
       +
Sparse BM25
       ↓
RRF
```

Measured:

```text
nDCG@10   = 0.9010
Recall@10 = 0.8378
MRR       = 0.9500
```

Among the evaluated configurations, the hybrid pipeline achieved the strongest measured retrieval performance.

---

# 8. Reranker Evaluation

A BGE reranker was evaluated as an additional ranking stage.

The measured result was:

```text
Hybrid:
nDCG@10   = 0.9010
Recall@10 = 0.8378
MRR       = 0.9500

Hybrid + Reranker:
nDCG@10   = 0.8532
Recall@10 = 0.6463
MRR       = 0.9250
```

The reranker therefore did not improve the measured retrieval metrics on this evaluation set.

As a result:

```text
Production path:
Hybrid Retrieval + Lightweight Ranking

Experimental:
Hybrid Retrieval + BGE Reranker
```

This prevents unnecessary model complexity from being introduced without evidence of improved retrieval quality.

---

# 9. Multilingual Evaluation

The system was evaluated separately across languages.

| Language | Queries | nDCG@10 | Recall@10 | MRR |
|---|---:|---:|---:|---:|
| English | 17 | 0.9433 | 0.8680 | 1.0000 |
| Tamil | 2 | 0.4914 | 0.5000 | 0.5000 |
| Hindi | 1 | 1.0000 | 1.0000 | 1.0000 |

---

## 9.1 English

The English subset contained 17 queries.

Measured:

```text
nDCG@10   = 0.9433
Recall@10 = 0.8680
MRR       = 1.0000
```

---

## 9.2 Tamil

The Tamil subset contained 2 queries.

Measured:

```text
nDCG@10   = 0.4914
Recall@10 = 0.5000
MRR       = 0.5000
```

The sample size is small, so this result should not be interpreted as a definitive measurement of Tamil performance.

It does, however, highlight the importance of expanding low-resource-language evaluation.

---

## 9.3 Hindi

The Hindi subset contained 1 query.

Measured:

```text
nDCG@10   = 1.0000
Recall@10 = 1.0000
MRR       = 1.0000
```

Because only one Hindi query was evaluated, this result should also be interpreted cautiously.

---

# 10. Evaluation Philosophy

The project follows:

> **Measure before adding complexity.**

The evaluation does not assume that:

- dense retrieval is always better
- sparse retrieval is always better
- hybrid retrieval is always better
- reranking is always better
- larger models automatically improve recommendation quality

Instead, alternative configurations are implemented and compared using the same evaluation methodology.

---

# 11. Evaluation Artefacts

Evaluation scripts are located under:

```text
backend/evals/
```

Generated reports are located under:

```text
backend/evals/reports/
```

Important reports include:

```text
retrieval_ablation_report.json
language_parity_report.json
```

---

# 12. Interpretation

The most important measured result is the difference between retrieval configurations.

The hybrid system achieved:

```text
nDCG@10   = 0.9010
Recall@10 = 0.8378
MRR       = 0.9500
```

This was stronger than the measured dense-only and sparse-only configurations.

The reranker experiment produced lower scores and therefore remains disabled in the production retrieval path.

The multilingual results also demonstrate that aggregate retrieval metrics should not be treated as sufficient evidence of language parity.

---

# 13. Evaluation Limitations

The current evaluation has several limitations:

1. The golden evaluation set is relatively small.
2. Language-specific subsets are uneven.
3. Tamil has only two evaluated queries.
4. Hindi has only one evaluated query.
5. The evaluation therefore provides useful engineering evidence but should be expanded before making broad claims about production-wide multilingual quality.

Future evaluation should increase:

- number of queries
- number of languages
- manually reviewed candidates
- filter-heavy queries
- vague queries
- multilingual coverage
- catalogue diversity

---

# 14. Future Evaluation Work

Potential extensions include:

- larger multilingual golden sets
- continuous evaluation in CI/CD
- online relevance feedback
- query-level latency evaluation
- cache-hit evaluation
- parser F1 evaluation
- explanation groundedness evaluation
- reliability/degradation testing
- larger catalogue benchmarks

The goal is to evolve from offline retrieval evaluation toward continuous system-level evaluation.
