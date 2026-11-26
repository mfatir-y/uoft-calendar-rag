# UofT Calendar RAG

A learning project: a retrieval-augmented question-answering tool over the
2026-27 University of Toronto Faculty of Arts & Science Academic Calendar
(artsci.calendar.utoronto.ca), with the retrieval pipeline written from
scratch in Python.

The full plan is in `docs/PLAN.md`. Read it before starting any task, and
follow its week-by-week order unless I say otherwise.

## Rules

- Hand-written only: chunking, similarity search (a NumPy matrix and a dot
  product), BM25, reciprocal rank fusion, prompt assembly, the eval harness.
- Do not add LangChain, LlamaIndex, a vector database (FAISS, Chroma, etc.),
  `rank_bm25`, or an evaluation framework such as Ragas.
- Borrowed on purpose: `requests` and `beautifulsoup4` for fetching and
  parsing, `sentence-transformers` with `BAAI/bge-small-en-v1.5`, and an LLM
  for writing answers (Ollama locally).
- Chunks are capped at about 450 tokens, counted with the embedding model's
  own tokenizer, heading path included.
- Every chunk keeps its canonical URL, page title, heading path and calendar
  year. Answers cite the source page.
- `eval/questions.json` is frozen. Never edit a question or reference answer
  to make a score go up. New questions go in a separate file.
- One change per experiment. Each run adds a row to `eval/results.md`.

## Scraping rules

- Fetch only the addresses listed in `scraper/urls.txt`. `discover.py` prints
  candidate links from an index page and never fetches them.
- At most one request per second, with a User-Agent that names the project
  and a contact address.
- Never request the search pages, or anything under `/admin/`, `/user/` or
  `/search/` (disallowed by the site's robots.txt).
- Cache raw HTML in `data/raw/` and work from the cache. Do not re-fetch a
  page that is already cached unless I ask.
- No PDF ingestion. The corpus is web pages only.

## Layout

```
scraper/  fetch.py, clean.py, discover.py, urls.txt
data/     raw/ (cached HTML), pages.json, chunks.jsonl, embeddings.npy
rag/      chunker.py, embedder.py, vector_index.py, bm25.py, hybrid.py,
          generate.py, ask.py
eval/     questions.json, run_eval.py, results.md
tests/    test_clean.py, test_chunker.py, test_bm25.py, test_hybrid.py
api/      main.py (FastAPI)
web/      chat page
docs/     PLAN.md
config.toml  LLM model, chunk cap, overlap, top-k, request delay
```

## Commands

These are the intended entry points. Update this section as they come to exist.

- Ask a question: `python -m rag.ask "question"`
- Run the evaluation: `python -m eval.run_eval`
- Run tests: `pytest`