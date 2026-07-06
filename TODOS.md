# Nomi To-Do List

This document compiles all TODO items, planned features, and known issues.

**Last Updated:** July 6, 2026

---

## Quick Access Links

- Main entry: `nomi.py`
- Menu system: `src/menu.py`
- Core logic: `src/brain.py`
- Providers: `src/providers/`
- Memory system: `src/memory/` *(planned)*
- Settings: `src/utils/cli.py`

---

## Provider Implementations

### Completed

- [x] Abstract `Provider` base class created
- [x] Gemini provider fully implemented
- [x] Local provider (Ollama / Qwen2.5) fully implemented
  - [x] Chat history loading from DB
  - [x] Provider/model mismatch detection (Gemini model name → auto-pick Ollama model)
- [x] Placeholder providers for OpenRouter, OpenAI, Anthropic
- [x] Settings menu: provider switching + live model search (questionary autocomplete)
- [x] API keys stored in `.env` file
- [x] Lazy provider loading to avoid unnecessary imports

### Pending

#### OpenRouter (`src/providers/openrouter.py`)
- [ ] Implement OpenRouter API integration
- [ ] Handle authentication via `OPENROUTER_API_KEY`
- [ ] Support model discovery from OpenRouter endpoints
- [ ] Implement streaming/non-streaming responses

#### OpenAI (`src/providers/openai.py`)
- [ ] Implement OpenAI API integration using `openai` package
- [ ] Handle authentication via `OPENAI_API_KEY`
- [ ] Support ChatGPT models (gpt-4o, gpt-4-turbo, etc.)

#### Anthropic (`src/providers/anthropic.py`)
- [ ] Implement Anthropic API integration using `anthropic` package
- [ ] Handle authentication via `ANTHROPIC_API_KEY`
- [ ] Handle Anthropic's message format (system as separate parameter)

#### General Provider Work
- [ ] Add rate limit handling per provider
- [ ] Implement proper error handling per provider (network, quota, key rotation)
- [ ] Add provider comparison/ranking for auto-upgrade
- [ ] Live streaming of responses (token-by-token output)

---

## Hybrid AI Backend: Implementation Plan

The core upgrade: Qwen2.5 (Ollama) as the conversational core, backed by vector semantic memory, document RAG, a curated facts store, and an optional vision pipeline. See `implementation_plan.md` for the full design.

### Phase 1: Semantic Event Memory *(Foundation)*

**Goal:** Every exchange is embedded and stored. Nomi can recall things from past sessions, even across different chats.

- [ ] Create `src/memory/` package (`__init__.py`)
- [ ] `src/memory/embedder.py`: wrap Ollama `/api/embeddings` with `nomic-embed-text`; fall back to `sentence-transformers` if Ollama unreachable
- [ ] `src/memory/store.py`: Chroma wrapper; one collection each for `events`, `docs`, `media`; upsert/query/delete
- [ ] `src/memory/memory_manager.py`: high-level API: `ingest_exchange()`, `search()`, `rebuild_index()`
- [ ] `src/brain.py`: hook `send_message()`: run `memory.search()` before provider call; `memory.ingest_exchange()` in background thread after reply
- [ ] `nomi.py`: on startup: if Chroma index missing, run one-shot backfill from SQLite `messages` table
- [ ] Add `memory:` section to `config.yaml` (enabled, embedding_model, chroma_path, top_k, min_score, token_budget, ingest_on_reply)
- [ ] Add `chromadb>=0.5.0` to `requirements.txt`

**Validation:** Say "My favorite number is 42", exit, reopen a *new* chat, ask "What's my favorite number?" - Nomi should recall it.

### Phase 2: Document RAG *(File Intelligence)*

**Goal:** Ingest PDFs, markdown, and text files; retrieve relevant chunks at query time.

- [ ] `src/memory/doc_ingestor.py`: `ingest_file()` / `ingest_dir()`; chunk 800 tokens / 20% overlap; PDF via `pypdf`; metadata: source_path, chunk_index, page_number, ingested_at
- [ ] `src/brain.py`: merge `events` + `docs` search results; deduplicate by source; keep top-6
- [ ] `src/menu.py`: add **Memory** section to Settings: Ingest file, Ingest folder, View index stats, Rebuild index
- [ ] Slash commands in `brain.handle_command()`:
  - [ ] `/ingest <path>`: ingest file or directory
  - [ ] `/recall <query>`: explicit deep search (top-10 with scores)
  - [ ] `/forget <id>`: delete a specific memory hit by ID
- [ ] Add `pypdf>=4.0.0` to `requirements.txt`

**Validation:** Drop a PDF, run `/ingest ./paper.pdf`, ask a question from its content, answer should cite the chunk.

### Phase 3: Facts Store *(Authoritative Knowledge)*

**Goal:** Human-curated, versioned facts that override model hallucination when confidence is high.

- [ ] Create `facts/` directory at repo root with YAML front-matter markdown format (`slug`, `title`, `confidence`, `source`, `last_verified`, `tags`)
- [ ] `src/memory/facts_store.py`: index `facts/` into `nomi_facts` SQLite table + embeddings; `sync()`, `query()`, `add_fact()`
- [ ] `src/brain.py`: facts lookup runs *first* in `send_message()`; if `confidence × similarity > 0.8`, prepend `[VERIFIED FACT]` block with citation
- [ ] Slash commands:
  - [ ] `/fact add`: interactive YAML + content prompt
  - [ ] `/fact list`: show all slugs + titles
  - [ ] `/fact sync`: re-index from `facts/` directory

**Validation:** Add a fact, ask a question that triggers it, response should include citation and not hallucinate.

### Phase 4: Vision Pipeline *(On-Demand)*

**Goal:** Caption images and extract keyframes from video; store captions in the `media` Chroma collection for semantic retrieval.

- [ ] `src/memory/vision.py`: `caption_image()`, `extract_keyframes()` (via `ffmpeg`, optional), `ingest_media()`; uses `qwen2.5-vl` or `llava` via Ollama; graceful fallback if no VL model pulled
- [ ] `src/brain.py`: query `media` collection in retrieval step; prepend `[IMAGE/VIDEO CONTEXT]` blocks with captions + source paths
- [ ] Extend `/ingest <path>` to route image/video extensions to `vision.ingest_media()`

**Validation:** Ingest a photo, ask something related to it - Nomi cites the caption.

### Phase 5: Context Builder & Prompt Assembly *(Polish)*

**Goal:** Consolidate all retrieval into a single token-budget-aware assembler; keep prompt clean and within limits.

- [ ] `src/memory/context_builder.py`: `build(query, chat_history, max_tokens)` → `PromptContext` dataclass; priority: facts > event memory > doc chunks > media
- [ ] `src/brain.py`: replace ad-hoc retrieval calls with single `context_builder.build()` call
- [ ] `src/providers/local.py`: add `inject_context(block: str)` method; prepends context as a `system` message separate from persona
- [ ] `Time context module`: detect morning/evening/weekend; add temporal awareness to responses
- [ ] `Decay weights for event memories`: stale items rank lower over time unless pinned

---

## CLI & UX

### Slash Commands
- [x] `/copy`: copy last AI response to clipboard *(requires `pip install pyperclip`)*
- [ ] `/switch`: switch between chats without returning to main menu
- [ ] `/search`: search across message history
- [ ] `/theme`: color theme switching (dark/light/retro presets)
- [ ] `/ingest <path>`: ingest file into memory *(Phase 2)*
- [ ] `/recall <query>`: explicit semantic search *(Phase 2)*
- [ ] `/forget <id>`: delete a memory hit *(Phase 2)*
- [ ] `/fact add / list / sync`: manage facts store *(Phase 3)*

### Chat Management
- [x] Display chat metadata in menu (last activity, message count)
- [ ] Message editing (update DB history)
- [ ] Chat search functionality

### UX Improvements
- [ ] Better error messages for API failures (network, quota, invalid key)
- [ ] Retry logic for transient errors
- [ ] Show chat size/word count in menu

---

## Technical Enhancements

- [ ] Live streaming of responses (token-by-token output for local + Gemini)
- [ ] Plugin system integration (scaffolding exists in `menu.py`)
- [ ] Remote triggers / scheduled agents
- [ ] Sync across devices (cloud backup)
- [ ] Single-window TUI (prototyped on `tui-branch`)
- [ ] Web scraping (`/fetch <url>` → fetch → summarize)
- [ ] Voice input/output (speech-to-text + TTS, platform-dependent)
- [ ] Multi-user chat (shared DB with user management)

---

## Known Issues / Technical Debt

1. **No response streaming** - `send_message()` blocks until full response; streaming would massively improve UX for large replies
2. **Hard-coded colors in `brain.py`** - user color `#b4befe`, Nomi color `green`; should come from config for theming
3. **Spinner flickers** - spinner uses `rich.status` which briefly flashes on some terminals; consider smoother frame-based indicator
4. **Menu loop blocking** - `main_menu()` is a while loop; could be refactored to a state machine for better testability
5. **Background model refresh** - threading implementation could have race conditions or resource leaks; needs stress testing
6. **Character limit is UI-only** - no server-side enforcement; long pastes bypass it silently
7. **`requirements.txt` was overwritten by user** - current `requirements.txt` appears to contain unrelated packages; needs to be restored to the correct Nomi dependency set

---

## Testing Checklist

### Passing
- [x] DB creation & migrations on fresh run
- [x] Terminal launch works on Linux/macOS
- [x] Slash commands execute correctly
- [x] Timestamps format correctly for today vs older
- [x] Character limit enforced (UI level)
- [x] Settings persist after exit
- [x] Chat rename handles duplicates gracefully
- [x] Delete confirmation works
- [x] Local (Ollama) provider connects and responds
- [x] Local provider carries chat history across messages within a session
- [x] Local provider loads DB history correctly on session resume
- [x] Provider/model mismatch auto-corrects (Gemini model name → Ollama model)

### Pending
- [ ] Test API failure scenarios (offline, invalid key, quota exceeded)
- [ ] Test very long messages (exceed character limit)
- [ ] Stress test with many chats (100+)
- [ ] Verify exported JSON and Markdown files are valid and complete
- [ ] Test provider switching (Gemini → OpenRouter/OpenAI/Anthropic)
- [ ] Test background model refresh thread for race conditions
- [ ] Memory Phase 1: cross-session recall after restart
- [ ] Memory Phase 2: doc chunk retrieval in responses
- [ ] Memory Phase 3: fact override with citation
- [ ] Memory Phase 4: image caption retrieval

---

## New Dependencies (Planned)

| Package | Version | Purpose | Phase |
|---------|---------|---------|-------|
| `chromadb` | ≥0.5.0 | Vector store (embedded, no server) | 1 |
| `pypdf` | ≥4.0.0 | PDF parsing for doc ingestor | 2 |
| `sentence-transformers` | ≥2.2.0 | CPU-only embedding fallback (optional) | 1 |

> Embedding: use `nomic-embed-text` via `ollama pull nomic-embed-text` (preferred, zero extra Python deps).
> Vision: use `qwen2.5-vl` or `llava` via Ollama (optional, pull on demand).
> Video keyframes: requires `ffmpeg` at OS level (optional, gracefully skipped).
