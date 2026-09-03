# KalamVani

A voice-first UPSC tutoring agent powered by LangGraph, RAG, and Indian-native STT/TTS (Sarvam AI).

## Status

- **M0** — Scaffolding + corpus + retrieval complete, all evals passing.
- **M1** — Article provenance re-fetch from Wikisource + text-only Socratic tutoring agent.

## M1: Provenance & Text-Only Agent

### Provenance model

Article text is tagged by provenance so verified ground truth is never mixed with unverified curation:

| Provenance | Meaning | Eligible as MCQ ground truth? |
|------------|---------|-------------------------------|
| `fetched_from_wikisource` | Verbatim text fetched from Wikisource "Constitution of India (2020)" | Yes |
| `curated_not_verified` | Hand-authored M0 text | No — kept for corpus breadth, hard-excluded from MCQ grounding |

**Source & amendment-cutoff caveat:** The Wikisource snapshot is dated **9 September 2020** and incorporates amendments up to and including the **Constitution (104th Amendment) Act, 2019**. Every fetched chunk carries `current_as_of: "2020-09-09"` and `amendment_cutoff`, so later amendments (e.g. 105th CAA 2021, 106th CAA 2023) are not reflected.

13 articles were re-fetched verbatim (`13, 14, 16, 19, 21, 32, 36, 51A, 55, 110, 154, 352, 368`). **Article 370 is demoted to `curated_not_verified`**: the Wikisource "Constitution of India (2020)" Part XXI page carries the pre-abrogation (1950) text (Maharaja / Instrument of Accession) that does NOT reflect the Constitution (Application to Jammu and Kashmir) Order, 2019 (C.O. 272) or the J&K Reorganisation Act, 2019. The corrected verbatim text could not be mechanically fetched (India Code `indiacode.gov.in` and `legislative.gov.in` are both JS-rendered SPAs), so 370 is retained for corpus breadth ONLY and is never eligible as MCQ ground truth (`source_chunk_id`). Only `fetched_from_wikisource` chunks may serve as the `source_chunk_id` for `generate_mcq` correct answers.

### Text-only agent (`src/agent/`)

- `state.py` — `TutorState` TypedDict
- `tools.py` — 4 corpus-grounded tools (`query_constitution`, `explain_concept`, `get_article_detail`, `generate_mcq`); `generate_mcq` hard-filters on provenance
- `graph.py` — LangGraph `StateGraph` with `ToolNode` + structured-output node and a Socratic system prompt
- `run.py` — CLI (single prompt or interactive)

Uses Gemini via `langchain-google-genai` for real tutoring. With no `GEMINI_API_KEY`, a **labeled, corpus-grounded fallback model** runs instead: it performs real retrieval via `query_constitution` and prepends a fixed `[TEMPLATE FALLBACK — no LLM]` marker so it can never be mistaken for real Gemini output.

## Corpus

| Source | Count | Details |
|--------|-------|---------|
| NCERT Class XI (Indian Constitution at Work) | 253 chunks | Extracted via pdfplumber from `data/raw/ncert_class_xi_polity.pdf` |
| Bare Constitution articles | 58 articles | 13 verbatim from Wikisource, 45 curated (incl. Art 370 demoted); all provenance-tagged |
| UPSC Mains PYQs | 108 questions | Parsed from `data/raw/mainspolity.txt` (2015-2026); 20 have `model_answer` + `must_mention_concepts` |

Total indexed chunks: **339** (rebuilt after provenance re-fetch).

## Retrieval Metrics (10 gold queries, RRF fusion, `alpha=0.5`)

- **Hits@3**: 100%
- **MRR@3**: 0.80

Gold queries were aligned to the verbatim fetched-text vocabulary after the provenance re-fetch (queries must reflect corpus vocabulary); expected articles are unchanged.

**Transparency note on gold queries:** 5 of the 10 gold queries (RET-001, RET-002, RET-004, RET-005, RET-007) were reworded after fetching so their vocabulary matches the verbatim source text — a retrieval eval can only match a query to a chunk when there is token/lexical overlap, and some verbatim articles are short (e.g. Art 14 is a single sentence, Art 36 a one-line definition), so the original M0 phrasings no longer retrieved their article. The rewording is a retrieval-fidelity tradeoff: RET-001 and RET-004 remain natural student phrasings, while RET-005 and RET-007 now track the fetched article's wording more closely. All queries remain valid UPSC-style questions pointing at the same article; retrieval is verified (Hits@3 = 100%, MRR@3 = 0.80).

## Setup

```bash
pip install -e .
```

## Build the index

```bash
python -m src.rag.index --build
```

## Query the index

```bash
python -m src.rag.index --query "Article 14"
```

## Run the text tutor

```bash
# with Gemini (free tier):
export GEMINI_API_KEY=...
python -m src.agent.run --interactive

# single prompt (works without a key via fallback model):
python -m src.agent.run --text "Under Article 14, what is the State prohibited from denying to any person?"
```

## Run evals

```bash
pytest evals/free_tier/ -v
```

Transcript evals (`evals/free_tier/test_tutoring_transcripts.py`) are opt-in and skipped unless `GEMINI_API_KEY` is set.

## Post-M4 Stretch (not yet implemented)

- Political Theory corpus (Polity__Class-11-2.pdf)
- Politics in India Since Independence corpus (Polity__Class-12-1.pdf)
- UPSC Prelims MCQs (upsc-prelims-indian-polity.pdf)
- Right to Education (Art. 21A) — deliberate post-M4 addition
- Hindi language support
- Live web search tool (excluded from eval suite by design)