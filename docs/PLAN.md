# UofT Calendar RAG: Project Plan

Nov 13, 2026 · @Fatir

## Summary

This is a question-answering tool over the Faculty of Arts & Science Academic Calendar, with every retrieval component written by hand in Python and a measured number behind each design choice.

Done means three things:

- **A working service.** A deployed `/ask` endpoint answers calendar questions with numbered citations that link to the source page, and says so when the calendar does not hold the answer.
- **An experiment log.** One table shows how each change (chunk size, BM25, hybrid search, re-ranking) moved retrieval and answer quality on a fixed question set.
- **Real usage.** Classmates have asked it questions and rated the answers.

## Scope

"From scratch" means you write every step between a web page and a prompt, and borrow only the neural models. No LangChain, LlamaIndex, vector database, BM25 package or evaluation framework.

| Component | Build or borrow | Notes |
| --- | --- | --- |
| Scraper and HTML cleaning | Build | `requests` and BeautifulSoup are plumbing, not retrieval, so using them is fine |
| Chunker | Build | Heading-aware, sized with the embedding model's own tokenizer |
| Vector index and similarity search | Build | A NumPy matrix and a dot product |
| BM25 keyword search | Build | Your own tokenizer, inverted index and scoring |
| Hybrid ranking | Build | Reciprocal rank fusion |
| Prompt assembly and citation checks | Build |  |
| Evaluation harness | Build |  |
| Embedding model | Borrow | bge-small-en-v1.5, loaded through sentence-transformers |
| Answer-writing LLM | Borrow | Ollama while developing, a hosted API once deployed |
| Re-ranker | Borrow, optional | A pretrained cross-encoder, tried as one experiment in week 4 |

Training your own embedding model stays out of scope. It is a different subject, and it would not improve retrieval on a corpus this small.

The embedding model is bge-small-en-v1.5 because it [accepts 512 tokens](https://developers.cloudflare.com/workers-ai/models/bge-small-en-v1.5/) and returns 384-dimension vectors. all-MiniLM-L6-v2 returns the same size of vector but [truncates at 256 word pieces](https://superlinked.com/glossary/what-is-all-minilm-l6-v2.md), which is too short for chunks of this size.

## Data source

The corpus is the 2026-27 Faculty of Arts & Science Academic Calendar at [artsci.calendar.utoronto.ca](https://artsci.calendar.utoronto.ca/), in effect since September 1, 2026. These facts were checked on the live site on November 13 and 14, 2026.

**How the scraper gets from page to page**

The scraper does not browse the site the way you do. It works through a list of addresses, so the only real question is how that list gets written. The site has three kinds of page:

| Kind of page | Examples | What the scraper does with it |
| --- | --- | --- |
| Index page | [Rules and Regulations](https://artsci.calendar.utoronto.ca/rules-and-regulations), [Degree Requirements](https://artsci.calendar.utoronto.ca/degree-requirements-hba-hbsc-bcom), [Program Areas A-Z](https://artsci.calendar.utoronto.ca/listing-program-subject-areas) | Nothing in week 1. It holds only links, so it is a place to find addresses, not text to index |
| Content page | The eight rule pages, HBA/HBSc Requirements, and one page per program area such as [Computer Science](https://artsci.calendar.utoronto.ca/section/Computer-Science) | Fetch, clean and chunk. This is the corpus |
| Detail page | One per course, such as `/course/CSC148H1`, and one per program, such as `/program/ASMAJ1689` | Leave for later. There are thousands |

There are three ways to write the list, and you need them in this order:

1. **By hand, in week 1.** The 16 addresses below go into `urls.txt`, and `fetch.py` loops over the file. There is no navigation at all.
2. **Link discovery, a small week 1 exercise.** `discover.py` fetches one index page, finds its main content area, collects every link inside it, turns relative links into full addresses, and prints those on the calendar's own host. Run on Program Areas A-Z it should print 114 program-area addresses. You read the output and paste what you want into `urls.txt`. The script never fetches what it finds.
3. **A crawl, later.** This is discovery repeated: a queue of addresses still to visit, a set of addresses already seen so nothing is fetched twice, and a depth limit so it stops. You need it only when course pages join the corpus.

**The starting list for `urls.txt`**

```
https://artsci.calendar.utoronto.ca/academic-record
https://artsci.calendar.utoronto.ca/course-enrolment
https://artsci.calendar.utoronto.ca/fees
https://artsci.calendar.utoronto.ca/graduation
https://artsci.calendar.utoronto.ca/off-campus-opportunities
https://artsci.calendar.utoronto.ca/petitions-and-appeals
https://artsci.calendar.utoronto.ca/term-work-tests-and-final-exams
https://artsci.calendar.utoronto.ca/withdrawal-and-return-absence
https://artsci.calendar.utoronto.ca/hbahbsc-requirements
https://artsci.calendar.utoronto.ca/rights-and-responsibilities
https://artsci.calendar.utoronto.ca/understanding-programs-and-certificates
https://artsci.calendar.utoronto.ca/understanding-courses
https://artsci.calendar.utoronto.ca/glossary-terms
https://artsci.calendar.utoronto.ca/Bachelor-of-Computer-Science
https://artsci.calendar.utoronto.ca/section/Computer-Science
https://artsci.calendar.utoronto.ca/section/Statistical-Sciences
```

The first eight are the Rules and Regulations pages. The last three cover computer science and statistics, including the Bachelor of Computer Science page that is new for 2026-27.

**What the pages look like**

- **Each page has two addresses.** `/node/16` and `/course-enrolment` return the same page. Read the canonical URL from each page and key everything on it, or the index will hold duplicates.
- **Rule pages are headings and lists.** The Course Enrolment page has no data tables. The chunker must keep a list together with the sentence that introduces it.
- **Program-area pages are long.** The Computer Science page is about 300,000 characters on one page, with no pagination. Each program sits under a title that carries its code, with "Enrolment Requirements" and "Completion Requirements" in bold beneath. Courses appear as linked codes. Only the first third of that page was read for this plan.
- **Two pages will supply most of the chunks.** Keep the program title in each chunk's heading path, or the Specialist, Major and Minor requirements will be hard to tell apart.
- **Boilerplate repeats.** The navigation menu, registrar contact block and land acknowledgement appear on every page and must be stripped before chunking.
- **Dates are elsewhere.** The calendar states rules but not dates. Drop deadlines sit on the Faculty's [Academic Dates page](https://www.artsci.utoronto.ca/current/dates-deadlines/academic-dates), a different site.
- **Search pages are not content.** Course Search, Program Search and Site Search return query results. Leave them out of every list.

**robots.txt, confirmed**

The file you pasted is the standard Drupal one. It disallows admin, search, login, registration and system paths, and sets no crawl delay. Nothing in it blocks the content pages, the `/section/` pages or the `/course/` pages.

**Not verified**

- **Terms of use.** The home page shows no terms-of-use statement, only a copyright line for the Faculty. This is not legal advice: link every answer back to its source page, quote short passages only, and label the tool unofficial.

**Scraping rules**

1. Fetch only the addresses in `urls.txt`. Discovery prints candidates, and you decide what goes in the file.
2. Send one request per second at most, with a User-Agent that names the project and a contact address.
3. Never request the search pages.
4. Cache the raw HTML on disk, so each page is fetched once and cleaning can be rerun offline.
5. Save one JSON record per page: canonical URL, title, heading tree, text, scrape date, content hash and calendar year.

## Build plan

Six weeks, each ending at a finish line you can check. Weeks 1 and 2 produce a complete but crude system. Weeks 3 and 4 improve it under measurement. Weeks 5 and 6 put it in front of people.

### Week 1: Scrape, clean, and start the question set

- Copy the starting list from the Data source section into `urls.txt`.
- Write `fetch.py` to download and cache raw HTML under the scraping rules above.
- Write `clean.py` to strip navigation and footer, then extract the title and a heading tree with the text under each heading. Test it on the Computer Science page, the longest and most deeply nested.
- Write `discover.py` and run it on the Program Areas A-Z page. It should print 114 addresses and fetch none of them.
- Write the first 20 evaluation questions as you read the pages. You are reading them closely this week anyway.

**Finish line:** `data/pages.json` holds every seed page, three pages checked by eye against the browser, and 20 questions exist.

### Week 2: Thin end-to-end version and baseline

- **Chunker.** Split on headings first. Pack paragraphs and list items into chunks up to the token cap, counted with the embedding model's tokenizer. Overlap by about 50 tokens only where one section is split in two.
- **Heading path.** Store each chunk's path, such as "Rules and Regulations > Course Enrolment > Course Load", and prepend it to the text before embedding. The path counts toward the cap.
- **Vector index.** Embed every chunk, normalize the vectors, and save them as one NumPy matrix beside a `chunks.jsonl` file. Search is a dot product followed by top-k selection.
- **Generation.** Number the top 5 chunks in the prompt. Instruct the model to answer only from them, cite like \[1\], and reply with one fixed sentence when the answer is missing.
- **Question set.** Finish all 50 questions, split them into development and held-out sets, and freeze both.
- **Baseline.** Run `run_eval.py` and record row 1 of the experiment log.

**Finish line:** `python -m rag.ask "question"` prints a cited answer, and `results.md` has a baseline row.

### Week 3: Keyword search, hybrid search, experiments

- **BM25.** Write a tokenizer that keeps course codes such as CSC207 and terms such as CR/NCR whole. Build an inverted index and score with the usual starting values, k1 between 1.2 and 2.0 and b = 0.75.
- **Hybrid.** Fuse the dense and BM25 rankings with reciprocal rank fusion: each chunk scores the sum of 1 / (60 + rank) across the two lists.
- **Unit tests.** Check BM25 and fusion against a three-document example worked by hand.
- **Experiments, one change at a time:** dense only, BM25 only, hybrid; chunk cap of 200, 350 and 450 tokens; heading path prepended or not; the bge query prefix on or off; top 3, 5 or 8 chunks.

**Finish line:** the experiment log has at least six rows, and the chosen configuration is the one the development set supports.

### Week 4: Answer quality

- **Citation checks in code.** Reject or flag any answer that cites a number not in the prompt, or cites nothing.
- **Refusals.** Compare two approaches: let the model decide, or refuse in code when the best retrieval score falls under a threshold.
- **Hand grading.** Grade accuracy and faithfulness for every question, using the rubric in the Evaluation section.
- **Optional re-ranker.** Retrieve 20 chunks, re-rank with a pretrained cross-encoder, keep 5. Log it as one more experiment.

**Finish line:** the final configuration has been run once on the held-out questions, with accuracy, faithfulness and no-answer results recorded.

### Week 5: API, interface, deployment

- **API.** A FastAPI `POST /ask` returns the answer plus a list of citations, each with URL, heading path and snippet. Load the model and index once at startup.
- **Cost protection.** Add a per-IP rate limit and a spending cap with the LLM provider. The endpoint is public and every call costs money.
- **Docker.** Install the CPU-only PyTorch build to keep the image small. Bake the index and model weights into the image so startup needs no downloads.
- **Hosting.** Deploy on Azure Container Apps or App Service.
- **Interface.** A chat page that shows each answer with links to its sources, plus a standing notice that the tool is unofficial and students should confirm with their registrar.
- **Change detection.** A scheduled GitHub Actions job re-fetches the seed pages, compares content hashes, and opens an issue when a page changed.

**Finish line:** a classmate can open a public URL and get a cited answer.

### Week 6: Real users

- Share it with classmates, course Discords and your co-op group.
- Add thumbs up and thumbs down to each answer.
- Log the question, answer, retrieved chunk IDs, rating and time against a random anonymous session ID. Store no names or IP addresses, show a "do not enter personal details" notice, and delete logs after a fixed period.
- Review the thumbs-down answers weekly. Add each real failure to a second, growing question set, kept apart from the frozen one.

**Finish line:** you can state the number of sessions and the share of rated answers that got a thumbs up.

### Later

- **More program areas.** Paste discovery output into `urls.txt` and rerun the pipeline. Rerun the evaluation too, to see how retrieval holds as the corpus grows.
- **Course pages.** Turn discovery into a crawl with a queue, a set of addresses already seen, and a depth limit.
- **Other sources.** Add the ASIP co-op pages and the Engineering, UTM and UTSC calendars.
- **Metadata filters.** Tag every chunk with faculty and calendar year, and filter on both at query time, so answers come from the right calendar.

## Evaluation

The evaluation is a frozen set of 50 questions, written before any tuning, that every version of the system is scored against. It is the part of the project that produces evidence, so it gets built early and changed never.

**The question set**

A suggested mix, to adjust once you have read the pages:

- **About 35 direct questions**, each answered by one section. Example: "How many credits can I take CR/NCR?"
- **About 7 hard questions**: exact terms and course codes, answers that span two sections, and questions whose answer is no. Example: "Can I take 8 courses in summer?"
- **About 8 questions the corpus cannot answer**, such as "Who teaches CSC311 this winter?" or "What room is my exam in?" Those live in the timetable and exam schedule, not the calendar.

Each record holds the question, a reference answer, the canonical URL and heading of the section that answers it, and a type:

```json
{
  "id": "q017",
  "type": "direct",
  "question": "What is the maximum course load in a summer term?",
  "reference_answer": "1.0 credit per term for students in good standing.",
  "gold_url": "https://artsci.calendar.utoronto.ca/course-enrolment",
  "gold_heading": "Course Load"
}
```

Copy each reference answer and heading from the live page as you write the record. The heading above is a placeholder.

Split the 50 into 35 development questions and 15 held-out questions. Tune on the development set only, and run the held-out set once, on the final configuration.

**Metrics**

| Metric | What it tells you | How it is scored |
| --- | --- | --- |
| Recall@5 | Whether the gold section is among the top 5 chunks | Automatic: match on canonical URL and heading |
| MRR | How high the first correct chunk ranks | Automatic: mean of 1 / rank |
| Answer accuracy | Whether the answer is right | By hand: correct, partly correct or wrong against the reference |
| Faithfulness | Whether every claim is supported by a cited chunk | By hand: yes or no per answer |
| Correct refusals | Whether it declines the unanswerable questions | Automatic: match the fixed refusal sentence |
| False refusals | Whether it declines questions it could have answered | Automatic: same match, on answerable questions |

Hand grading 50 answers per run is slow, so run the two automatic retrieval metrics on every experiment and hand grade only the configurations you are choosing between.

**Reading the numbers**

- With 50 questions, one question is 2 percentage points. A score near 80% carries a margin of roughly 11 points either way at 95% confidence.
- Report counts beside percentages, such as 41 of 50, and treat a gap of one or two questions as noise.
- Grow the set toward 100 questions before claiming a small improvement.
- Hold the LLM, prompt and temperature fixed while tuning retrieval, so a change in accuracy has one cause.

**The experiment log**

`results.md` is one table with a row per run: run number, the single thing that changed, Recall@5, MRR, and accuracy and faithfulness where graded. Record the baseline before changing anything. Resume figures come from the first and last rows of this table.

## Project structure

One Python package per stage, with data files between stages, so any stage can be rerun without the ones before it.

```
uoft-rag/
  CLAUDE.md   short standing rules for Claude Code
  docs/       PLAN.md (this plan, exported)
  scraper/    fetch.py, clean.py, discover.py, urls.txt
  data/       raw/ (cached HTML), pages.json, chunks.jsonl, embeddings.npy
  rag/        chunker.py, embedder.py, vector_index.py, bm25.py,
              hybrid.py, generate.py, ask.py
  eval/       questions.json, run_eval.py, results.md
  tests/      test_clean.py, test_chunker.py, test_bm25.py, test_hybrid.py
  api/        main.py (FastAPI)
  web/        chat page
  Dockerfile
  pyproject.toml
  README.md
```

**Building the index, run once per scrape**

1. `fetch.py` downloads the seed pages into `data/raw/`.
2. `clean.py` turns raw HTML into `pages.json`.
3. `chunker.py` turns pages into `chunks.jsonl`.
4. `embedder.py` writes `embeddings.npy`, and `bm25.py` builds its inverted index from the same chunks.

**Answering a question, run per request**

1. Embed the question and take the top 20 chunks by dot product.
2. Score the question with BM25 and take its top 20.
3. Fuse the two rankings in `hybrid.py` and keep the top 5.
4. `generate.py` builds the numbered prompt, calls the LLM, and checks the citations.

**Dependencies:** `requests`, `beautifulsoup4`, `numpy`, `sentence-transformers`, `fastapi`, `uvicorn`, `pytest`, and one LLM client.

## Open decisions

Five choices are yours to make, the first two before any code is written.

- [ ] **Confirm the starting list.**

  Sixteen addresses are suggested in the Data source section. Decide whether the BCom Requirements page joins them, and whether the glossary earns its place.
- [ ] **Decide whether the Academic Dates page joins the corpus.**

  Suggested: yes, as one extra page with its own source label, because deadline questions are an obvious use. It is on a different site, so read that site's robots.txt first. If it stays out, the right answer to a deadline question is the rule plus a pointer to that page.
- [ ] **Pick the hosted LLM for the deployed version.**

  Ollama suits development because it is free and local. A small cloud container is unlikely to run a local model at usable speed, so the public version needs a hosted API with a spending cap.
- [ ] **Pick the interface.**

  If the goal is an all-Python project, one static HTML page served by FastAPI is enough for a chat box and a list of sources. Choose Next.js if you want it shown on the resume.
- [ ] **Set the log retention period.**

  Any fixed number works. State it on the page.

## Sources

- [Arts & Science Academic Calendar home page](https://artsci.calendar.utoronto.ca/): calendar year, effective date, link to Academic Dates
- [How to Use the Calendar](https://artsci.calendar.utoronto.ca/how-use-calendar): the address of every navigation link
- [Rules and Regulations](https://artsci.calendar.utoronto.ca/rules-and-regulations): subsection list and page structure
- [Course Enrolment](https://artsci.calendar.utoronto.ca/course-enrolment): summer course load, canonical URL, absence of dates
- [Listing of Program/Subject Areas](https://artsci.calendar.utoronto.ca/listing-program-subject-areas): 114 linked program areas and their address pattern
- [Computer Science](https://artsci.calendar.utoronto.ca/section/Computer-Science): layout of a program-area page, first third only
- [PDF Version of 2026-27 Calendar](https://artsci.calendar.utoronto.ca/pdf-version-current-calendar) and [Archived Calendars](https://artsci.calendar.utoronto.ca/archived-calendars): PDF availability
- robots.txt for artsci.calendar.utoronto.ca, as pasted by you on November 13, 2026
- [Cloudflare Workers AI: bge-small-en-v1.5](https://developers.cloudflare.com/workers-ai/models/bge-small-en-v1.5/): input limit and vector size
- [Superlinked: all-MiniLM-L6-v2 reference](https://superlinked.com/glossary/what-is-all-minilm-l6-v2.md): 256 word piece limit
