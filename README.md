# UofT Calendar RAG

A question-answering tool over the 2026-27 University of Toronto Faculty of
Arts & Science Academic Calendar. Chunking, vector search, BM25, rank fusion,
prompt assembly and evaluation are written from scratch. Only the embedding
model (`BAAI/bge-small-en-v1.5`) and the answer-writing LLM are borrowed.

Unofficial. Always confirm answers with your registrar.

The full plan is in [docs/PLAN.md](docs/PLAN.md).

## Setup

Requires Python 3.11 or newer and [Ollama](https://ollama.com/download).

1. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   # Windows (PowerShell)
   .venv\Scripts\Activate.ps1
   # macOS / Linux
   source .venv/bin/activate
   ```

2. Install the project with its dev tools:

   ```bash
   pip install -e ".[dev]"
   ```

   Optional: if you have no NVIDIA GPU, install the much smaller CPU-only
   PyTorch build first:
   `pip install torch --index-url https://download.pytorch.org/whl/cpu`

3. Pull the Ollama model named in `config.toml`:

   ```bash
   ollama pull llama3.2:3b
   ```

4. Check the install:

   ```bash
   pytest
   ```

## Usage

- Ask a question: `python -m rag.ask "question"`
- Run the evaluation: `python -m eval.run_eval`
- Run tests: `pytest`

Settings (LLM model, chunk size, overlap, top-k, request delay) live in
`config.toml`.
