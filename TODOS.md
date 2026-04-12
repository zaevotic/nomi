# Nomi To-Do List

This document compiles all TODO items, planned features, and known issues from the codebase and development plan.

**Last Updated:** April 8, 2026 *(Updated: Verified all source files against TODO items)*

---
*Note: This verification was performed by examining all source files in the src/ directory and cross-referencing with existing TODO comments, revamp_plan.md, and README.md. Items marked as completed have been verified against actual implementation.*

---

## Feature TODOs (from Code Comments)

### Provider Implementations

#### OpenRouter (`src/providers/openrouter.py`)

- [ ] Implement OpenRouter API integration
- [ ] Handle authentication via `OPENROUTER_API_KEY`
- [ ] Support model discovery from OpenRouter endpoints
- [ ] Implement streaming/non-streaming responses
- [ ] Handle provider-specific features (params, pricing, etc)

#### OpenAI (`src/providers/openai.py`)

- [ ] Implement OpenAI API integration using `openai` package
- [ ] Handle authentication via `OPENAI_API_KEY`
- [ ] Support ChatGPT models (gpt-4, gpt-3.5-turbo, etc.)
- [ ] Implement streaming and function calling if needed

#### Anthropic Claude (`src/providers/anthropic.py`)

- [ ] Implement Anthropic API integration using `anthropic` package
- [ ] Handle authentication via `ANTHROPIC_API_KEY`
- [ ] Support Claude models (claude-3-opus, claude-3-sonnet, claude-3-haiku)
- [ ] Handle Anthropic's message format (system as separate parameter)

---

## Planned Features (from `.claude/revamp_plan.md`)

### Missing from README Scope

- [ ] Vector database / RAG integration
- [ ] Multi-user chat support
- [ ] Web scraping capability (`/fetch <url>`)
- [ ] File upload support (images, documents)
- [ ] Voice capabilities (input/output)
- [ ] Full-window TUI (single-window alternative to multi-window CLI)
- [ ] Plugin system integration (scaffolding exists in menu.py)

### Slash Commands

- [ ] `/switch` - Switch between chats without returning to menu
- [x] `/copy` - Copy last AI response to clipboard (pyperclip optional dependency) - *Implemented, requires `pip install pyperclip`*
- [ ] `/theme` - Color theme switching
- [ ] `/search` - Search across messages

### Chat Management

- [ ] Message editing (DB history updates)
- [ ] Chat search functionality
- [x] Display chat metadata in menu (last activity, message count) - *Implemented in chat selection screen*

### UX Improvements

- [ ] Better error messages for API failures (network, quota)
- [ ] Retry logic for transient errors
- [ ] Graceful handling of missing/changed API key
- [ ] Chat rename validation (prevent duplicates) - *Already implemented*
- [ ] Show chat size/word count in menu - *Could be added to chat metadata display*

### Technical Enhancements

- [ ] Live streaming of responses (Gemini streaming API)
- [ ] Single-window TUI (prototyped on `tui-branch`)
- [ ] Plugin system integration (scaffolding exists in menu.py)
- [ ] Remote triggers / scheduled agents
- [ ] Sync across devices (cloud backup)

---

## Testing Checklist

- [x] DB creation & migrations on fresh run
- [x] Terminal launch works on Linux/macOS/Windows
- [x] Slash commands execute correctly
- [x] Timestamps format correctly for today vs older
- [x] Character limit enforced
- [x] Settings persist after exit
- [x] Chat rename handles duplicates gracefully
- [x] Delete confirmation works
- [ ] Test API failure scenarios (offline, invalid key, quota exceeded)
- [ ] Test very long messages (exceed character limit, test truncation)
- [ ] Stress test with many chats (100+)
- [ ] Verify exported JSON and Markdown files are valid and complete
- [ ] Test provider switching (Gemini → OpenAI/Anthropic/OpenRouter) when implemented
- [ ] Test background model refresh thread doesn't cause race conditions

---

## Known Issues / Technical Debt

1. **Spinner in chat windows**: Uses `rich.status` which briefly flashes; consider smoother indicators
2. **No response streaming**: `generate_response` blocks until full response; could use Gemini streaming API for real-time output
3. **Hard-coded colors in brain.py**: `#b4befe` for user, `green` for Nomi; should come from config for theming
4. **Menu loop blocking**: `main_menu()` is a while loop; could be refactored to state machine for better testability
5. **Terminal detection can fail**: If unknown terminal, user must manually set `default_terminal` in config
6. **Copy command requires pyperclip**: Already shows helpful error message; consider making it a dependency or providing clearer install instructions
7. **Background model refresh**: Threading implementation could have race conditions or resource leaks - needs testing
8. **Character limit enforcement**: Only UI-level; could add server-side validation for safety

---

## Multi-Provider Architecture (Current State)

### Completed ✅

- [x] Abstract `Provider` base class created
- [x] Gemini provider fully implemented
- [x] Placeholder providers for OpenRouter, OpenAI, Anthropic
- [x] Settings menu consolidation (Persona, Appearance, Model Selection, API, Plugins)
- [x] Model selection with provider switching
- [x] API keys stored in `.env` file
- [x] Lazy provider loading to avoid unnecessary imports

### Next Steps for Multi-Provider

- [ ] Implement OpenRouter API integration (allows access to many models)
- [ ] Implement OpenAI API integration
- [ ] Implement Anthropic API integration
- [ ] Add provider-specific configuration (base URLs, extra headers)
- [ ] Implement proper error handling per provider
- [ ] Add rate limit handling per provider
- [ ] Implement model discovery/listing from provider APIs
- [ ] Add provider comparison/ranking for auto-upgrade

---

## Quick Access Links

- Main entry: `nomi.py`
- Menu system: `src/menu.py`
- Core logic: `src/brain.py`
- Providers: `src/providers/`
- Settings: `src/utils/cli.py`
- Development plan: `.claude/revamp_plan.md`

---

## Development Roadmap (from revamp_plan.md)

### Priority 1: Polish CLI Experience

- [ ] Add `/switch` command to quickly jump between chats without returning to menu
- [ ] Add `/theme` command for basic color theme switching (maybe dark/light/retro presets)
- [ ] Implement chat search (`/search <query>` or separate screen)
- [x] Add `/copy` to copy last AI response to clipboard (handle pyperclip optional) - *Already implemented*

### Priority 2: Stability & Ergonomics

- [ ] Better error messages when API fails (network issues, quota)
- [ ] Retry logic for transient errors
- [ ] Graceful handling of missing/changed API key
- [ ] Chat rename validation (no duplicates) - *Already implemented*
- [ ] Show chat size/word count in menu - *Could be added to chat metadata display*

### Priority 3: External Memory System (Obsidian-like Interface)

- [ ] Note system architecture - *Markdown-based notes with unique IDs and metadata (title, created, tags)*  
- [ ] Link parser - *Parse and extract [[wikilinks]] and #tags from note content*
- [ ] Graph database - *Build relationship graph between notes using NetworkX*
- [ ] Vector embeddings - *Generate embeddings for semantic similarity search (sentence-transformers or OpenAI)*
- [ ] FAISS vector store - *Store and query note embeddings efficiently*
- [ ] Graph-based memory expansion - *Auto-expand queries via linked notes (1-hop, 2-hop)*
- [ ] Bi-directional links - *Store forward links AND backlinks automatically*
- [ ] Tag-based indexing - *Index #tags for quick category-based retrieval*
- [ ] Note creation interface - *Add notes via chat commands or UI (`/note create`)*
- [ ] Note visualization - *Basic graph view or ASCII tree of note relationships*
- [ ] Semantic search - *Find similar concepts using vector similarity*
- [ ] Auto-linking suggestions - *Suggest related existing notes when creating new ones*
- [ ] Note CRUD operations - *Create, read, update, delete notes with proper history*
- [ ] External note storage - *Store notes in organized directory structure (`notes/`)*
- [ ] Note linking from chat - *Mention notes in conversation using [[note name]] syntax*

### Priority 4: Environment Awareness & Context Building

- [ ] Context Builder architecture design - *Design system to merge memory, time, external data into structured context*
- [ ] Time context integration - *Add relative time (morning/evening) and temporal awareness to responses*
- [ ] Local file read-only access - *List, read, and search files without writing*
- [ ] Web integration - *Controlled web search → fetch → summarize workflow*
- [ ] Multi-source context merging - *Combine memory + time + external data into unified context*
- [ ] Context-aware response formatting - *Adjust responses based on all available context*
- [ ] Context scoring/ranking - *Prioritize most relevant context pieces for token budget*

### Priority 5: Advanced Features (from README)

- [ ] Vector database integration for memory/context retrieval - *Implement using FAISS (already in Priority 3)*
- [ ] File attachment support (images, documents) - *Upload and reference files in notes/chats*
- [ ] Web scraping (`/fetch <url>`) - *Fetch and summarize web content*
- [ ] Multi-user chat (invite others, shared DB?) - *Shared database with user management*
- [ ] Voice input/output (optional, platform-dependent) - *Speech-to-text and TTS*

### Future Consideration

- [ ] Single-window TUI (already prototyped on `tui-branch`, may be merged later if desired)
- [ ] Plugin system (scaffolding exists but not integrated)
- [ ] Remote triggers / scheduled agents
- [ ] Sync across devices (cloud backup)

---

## External Memory System: Implementation Sequence (Critical Path)

### Phase 1: Note System Foundation

1. Define note schema (id, title, content, links, tags, timestamps)
2. Create note directory structure (`notes/` folder)
3. Build markdown parser with [[wikilink]] extraction
4. Implement note CRUD commands (`/note create`, `/note edit`, `/note delete`)
5. Store note metadata alongside markdown files

### Phase 2: Graph Construction

6. Add NetworkX dependency
7. Build graph builder: parse all notes → extract edges from [[links]]
8. Store graph structure (in-memory + persist to disk as JSON)
9. Implement graph traversal (get linked notes, find paths)
10. Generate adjacency lists for quick expansion

### Phase 3: Vector Layer

11. Add sentence-transformers or OpenAI embeddings dependency
12. Generate embeddings for every note (batch process existing notes)
13. Set up FAISS index for fast similarity search
14. Implement semantic search: "find notes similar to X"
15. Store embedding vectors alongside notes

### Phase 4: Retrieval Integration

16. Build unified retrieval function: `(query) → relevant_notes`
17. Combine vector search + graph expansion (retrieve → expand 1-2 hops)
18. Return structured context: `{primary, related, timeline}`
19. Test with messy human queries ("that mars thing")
20. Tune search parameters (top-k, expansion depth)

### Phase 5: Context Builder

21. Add time context module (detect morning/evening/weekend)
22. Design context merging algorithm (priority ranking)
23. Format context for LLM consumption (token budgeting)
24. Plug structured context into Nomi's prompt (brain.py)
25. Verify Nomi can reference specific notes in responses

### Phase 6: UI Integration

26. Add note commands (`/note list`, `/note show <id>`, `/note search`, `/note tag <tagname>`)
27. Show note references in chat UI (when Nomi cites a note with `[[link]]`)
28. Add ability to create notes from chat (save exchange as note: `/note save`)
29. Simple graph visualization (text-based tree or ASCII art, `mermaid` diagram in markdown)
30. Nomi auto-references: When Nomi recalls something from notes, show subtle `[note: Title]` attribution
31. Note index rebuild command (for when many notes change) (`/note reindex`)

### Phase 7: Integration & Testing

32. Plug Context Builder into Brain's message generation pipeline
33. Inject structured context into LLM prompt with proper role separation (think: "Here's what I know from memory...")
34. A/B test: Compare quality with/without external memory
35. Stress test with 1000+ notes (measure recall + graph traversal performance)
36. User testing: Verify Nomi can "answer from notes" consistently
37. Add tests for link extraction, graph traversal, and vector search edge cases

---

## Key Design Decisions to Make (Open Questions)

1. **Embedding model**: sentence-transformers (local) vs OpenAI (API)? Trade-off: quality vs cost/latency
2. **Note storage**: pure markdown files vs SQLite table for metadata? Trade-off: human-readable vs queryable
3. **Graph persistence**: in-memory NetworkX + disk serialization vs dedicated graph DB (Neo4j)?
4. **Link syntax**: `[[note title]]` vs `#tag` vs custom? Stick with Obsidian format for compatibility?
5. **Sync model**: Background embedding generation on demand vs pre-compute all?
6. **Context window**: How many notes to include? Dynamic based on token count?

---

## Early Validation Criteria

Once Phase 1-2 are done, validate by:
```
Query: "What did I write about Mars?"
Expected: Returns note ID(s) containing "Mars" + linked notes (even if link text doesn't say "Mars")
```

Once Phase 3 is done, validate by:
```
Query: "That conspiracy theory note"
Expected: Returns the note even if exact words don't match (semantic hit)
```

Once Phase 4 is done, validate by:
```
Context output is: { "primary": [1,2], "related": [3,4,5], "timeline": [...] }
Brain uses it to produce informed responses.
```

Stop here — don't overbuild. If this works, proceed to Phase 5.

---

## Obsidian vs. Nomi External Memory: Key Differences

| Aspect | Obsidian | Nomi's System |
|--------|----------|---------------|
| **Data Source** | Static markdown files (user-written) | Dynamic memory (conversation + notes) |
| **Linking** | Manual `[[links]]` | Auto-suggested + manual |
| **Understanding** | None (just storage) | AI-powered retrieval & response |
| **Graph** | Visual only (manual exploration) | Invisible backbone (auto-expansion) |
| **Search** | Text-based + plugins | Vector-semantic + graph expansion |
| **Action** | Read-only reference | Active participant (talks back) |
| **Evolution** | Manual curation | Auto-generated links + semantic clustering |

**Philosophical difference:**

- Obsidian = **second brain** for a human to reference
- Nomi = **living brain** that uses notes as part of its cognition

**Implementation Checkpoint:** Only move to the next phase if the current one passes validation. Don't build ahead — build surgically.

---

## Technical Dependencies to Add

### Phase 1-2 (Graph)

```python
networkx>=3.0  # For graph construction and traversal
```

### Phase 3 (Vectors)

```python
sentence-transformers>=2.0  # Local embedding generation (offline, private)
OR
openai>=1.0  # For OpenAI embeddings (higher quality, paid)
faiss-cpu>=1.7  # For fast nearest-neighbor search
```

### Phase 5-6 (UI)

```python
rich  # Already used - extend for better note display
prompt_toolkit  # Already used - add autocompletion for note names
```

**Suggested baseline:** Start with `sentence-transformers` + `faiss-cpu` for a fully local, private setup.

---

## File Structure (where things live)

```
nomi/
├── notes/                  # External memory storage
│   ├── 001_martian_moonlight_conspiracy.md
│   ├── 002_identity_theory.md
│   └── ...
├── notes_index.json        # Note metadata (id, title, path, tags)
├── notes_graph.json        # NetworkX adjacency {node_id: [linked_ids]}
├── notes_vectors/          # FAISS index + mapping files
│   ├── index.faiss
│   └── id_mapping.pkl
└── src/
    ├── notes/              # New module for memory system
    │   ├── __init__.py
    │   ├── parser.py       # Markdown + wikilink extraction
    │   ├── graph.py        # NetworkX graph builder
    │   ├── vectors.py      # Embedding + FAISS
    │   ├── retrieval.py    # Unified retrieval function
    │   └── cli.py          # /note commands
    └── brain.py            # Modified to accept external context
```

---

## What "Retrieval is Stable" Actually Looks Like

When testing shows:

```
You: "that mars thing"
Nomi: "You're referring to Martian Moonlight Conspiracy [note #1]...
       It's linked to Identity Theory [note #3] and Human Evolution [note #7]."
```

See that? Nomi named the note, cited IDs, and mentioned linked notes.

**That's the checkpoint.** Once you can do that consistently (even with vague queries), you are ready to layer time → files → web on top.

---

**Final note:** You're not building a note-taking app. You're building memory infrastructure for an AI that thinks. Build only what it needs to think clearly.

