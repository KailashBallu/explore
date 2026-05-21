# Meeting Intelligence — Development Plan

> **Version:** 1.1  
> **Date:** 2026-05-18  
> **Status:** Planning

---

## 1. Overview

This document outlines the phased development approach for building the Meeting Intelligence platform — a meeting minutes generation tool for formal corporate meetings.

**Total phases:** 6 (5 core + 1 future)  
**Target MVP:** Phase 0–5 complete

---

## 2. Development Phases

### Phase 0: Project Scaffolding & Infrastructure

**Goal**: Reproducible dev environment and CI pipeline.

- Initialize Python project (FastAPI, LangGraph, LangChain, Celery, deps)
- Initialize React project (Vite, Tailwind, shadcn/ui, routing)
- Docker Compose dev environment (PostgreSQL, Redis, MinIO)
- DB migrations setup (Alembic)
- CI pipeline (GitHub Actions: lint, type-check, test)

**Deliverable**: `docker compose up` spins up the full dev environment.

---

### Phase 1: Core Backend — Meetings & Files

**Goal**: API to manage meetings, files, and users.

- User auth (register, login, JWT access/refresh tokens)
- Meeting CRUD (metadata, attendees, agenda)
- File upload/download with S3-compatible storage (MinIO in dev)
- Lifecycle policy for 30-day auto-delete on object storage
- Celery worker setup (broker config, task routing)

**Deliverable**: REST API for creating meetings, uploading files, managing metadata. Authenticated endpoints working.

**Key API endpoints:**
```
POST /api/auth/login, /api/auth/refresh, /api/auth/logout
GET/POST /api/meetings
GET/PUT/DELETE /api/meetings/:id
POST /api/meetings/:id/upload
```

---

### Phase 2: Transcription & Provider Integration

**Goal**: Convert recordings into structured transcripts with timestamps and speaker labels.

- Provider abstraction layer (transcription interface + LLM interface)
- **Media preprocessing pipeline** (ffmpeg):
  - Extract audio stream from video containers (`.mp4`, `.mov`, `.avi`, `.mkv`, `.webm`)
  - Audio format transcoding: accept arbitrary codecs (MP3, AAC, Opus, Vorbis, WMA, FLAC, etc.), output 16kHz mono FLAC
  - Sample rate normalization: resample to 16kHz regardless of input (upsample low-rate conference recordings, downsample 44.1/48kHz)
  - Channel reduction: stereo/multi-channel → mono
  - Validation: silent/empty audio detection, provider size limit checks, duration verification
  - Temp storage for normalized file, cleanup after transcription
- Recording → transcription via Deepgram (primary) or OpenAI Whisper (fallback)
  - Word-level timestamps
  - Speaker diarization
- Transcript parsing and timestamp detection
  - Support formats: `HH:MM:SS`, `[00:00]`, `<00:00:00>`, SRT, VTT
  - Graceful handling when no timestamps found

**Deliverable**: Upload a recording in any common format → get a transcript with timestamps and speaker labels stored in DB and object storage.

---

### Phase 3: LangGraph Minutes Generation Graph

**Goal**: Multi-step agentic workflow that transforms transcript + metadata into structured minutes with automated quality evaluation.

- Define `MinutesState` TypedDict and state schema
- Implement all 11 graph nodes:
  - `validate_input` — deterministic validation
  - `preprocess_media` — ffmpeg: extract audio, normalize to 16kHz mono
  - `transcribe` — transcription service call
  - `process_transcript` — parse uploaded transcript
  - `align_agenda` — LLM: map agenda items to transcript segments
  - `summarize_agenda_item` — LLM: per-agenda-item summarization
  - `extract_motions` — LLM: extract formal motions/resolutions
  - `extract_action_items` — LLM: extract action items
  - `extract_next_meeting` — LLM: extract next meeting info
  - `assemble_minutes` — deterministic: compile into JSONB
  - `validate_minutes` — deterministic structural checks + quality gate with retry loop
- Wire conditional edges (recording vs transcript branch, validation pass/fail)
- Implement `Send()` fan-out for parallel agenda item summarization
- Configure `PostgresSaver` checkpointing
- Wire `astream_events()` progress streaming → Redis pub/sub
- **Evaluation — Automated scoring**:
  - Deterministic structural checks in `validate_minutes`
  - LLM-as-judge evaluation node that scores each section post-generation (separate model/call)
  - Store scores in `generation_evals` table
  - Return scores alongside minutes to frontend
- Celery task that instantiates and runs the graph

**Deliverable**: Celery task accepts meeting_id → LangGraph workflow runs end-to-end → structured minutes with traceability links AND quality scores stored in DB.

---

### Phase 4: Frontend — Upload & Review

**Goal**: Full browser-based user experience from meeting creation to minutes review.

- Dashboard & meeting list with status badges
- Upload wizard (5-step form with validation and auto-save)
- Real-time processing status via WebSocket (progress bar with step name)
- Review editor: side-by-side layout
  - Left panel: editable minutes with rich-text fields
  - Right panel: transcript view with synchronized audio player
  - Hover-to-highlight linking between minutes and transcript
  - Click-to-replay from timestamp (when available)
- In-app editing with auto-save (debounced save to API)

**Deliverable**: End-to-end flow working in the browser — create meeting, upload input, watch generation progress, review and edit minutes with source linking.

---

### Phase 5: Export, Polish & User-Facing Evaluation

**Goal**: Production-grade quality, export capabilities, and user-facing evaluation features.

- DOCX export with professional formatting (headings, tables, page numbers)
- PDF export (via WeasyPrint from DOCX)
- Version history for minutes (list versions, view diffs, restore)
- **User-facing quality scores**:
  - Display per-section scores (dots + numeric) in review editor
  - Highlight sections below quality threshold
  - Aggregate meeting-level quality indicator on dashboard
- **User feedback collection**:
  - Per-section thumbs up/down, flag for review, free-text notes
  - Per-meeting satisfaction rating
  - Store feedback in `section_feedback` table for analysis
- **Style customization via samples**:
  - User uploads 1–3 example minutes they consider "gold standard"
  - LLM extracts style profile (conciseness, formality, detail density, structure)
  - Style profile injected into generation prompts
  - Re-generate respects the learned style
- Error handling & edge cases:
  - Long meetings (>4 hours): increased chunking, per-chunk progress
  - No timestamps in uploaded transcript: disable replay, show warning
  - Transcription failures: retry with backoff, user notification
  - LLM rate limits: queue management, graceful degradation
- Loading states, empty states, and error boundaries in UI

**Deliverable**: Production-grade MVP with quality scoring, user feedback loop, and style customization. Ready for user testing.

---

### Phase 6 (Future): Chat Interface, Integrations, Multi-user

**Goal**: Extend the platform with alternative interfaces and enterprise features.

- Chat-based UI for meeting creation and review
  - Natural language upload: "Generate minutes for the Acme Corp board meeting on May 15..."
  - Review assistant: "Rewrite the discussion summary for agenda item 3..."
- Calendar integration (Outlook, Google Calendar)
- Video conferencing integration (Zoom, Teams, Google Meet)
- Multi-user organizations with roles (admin, secretary, viewer)

---

## 3. Verification Plan

### 3.1 Functional Testing (end-to-end)
1. Create a test meeting with full metadata, attendees, agenda
2. Upload a sample recording (pre-recorded mock board meeting, ~20 min) in **video format (MP4)** — verify audio extraction and normalization
3. Repeat with **audio-only formats** (MP3, WAV at various sample rates) — verify normalization to 16kHz mono
4. Verify transcription includes timestamps and speaker labels
5. Trigger generation, verify all section types appear in output
6. In review editor: click a generated point, verify transcript highlights correctly
7. Click replay, verify recording plays from correct timestamp
8. Edit a discussion summary in the editor, verify auto-save
9. Export as DOCX and PDF, verify formatting
10. Upload transcript-only (no timestamps), verify minutes still generate without replay
11. Upload transcript with timestamps, verify traceability works
12. Wait 30+ days (or manually trigger lifecycle), verify file deletion

### 3.2 Technical Testing
- **Unit tests**: provider abstraction, timestamp detection, individual graph nodes (mock LLM), JSONB minutes assembly, state reducer (`operator.add`), deterministic structural checks, LLM-as-judge scoring schema, **media preprocessing (ffmpeg pipeline: video demuxing, format transcoding, sample rate conversion, channel reduction, silent audio detection)**
- **Graph structural tests**: verify graph compiles without cycles, conditional edges route correctly, `Send()` fan-out count matches agenda items
- **Integration tests**: full graph invocation with mocked LLM calls, Celery task dispatch + result, file upload/download, auth flow, checkpoint save/restore on simulated crash
- **LLM output validation**: schema conformance, source range bounds checking
- **Progress streaming**: verify Redis pub/sub messages emitted at each node transition
- **Performance**: <5 min total processing for a 2-hour meeting (parallel LLM calls via Send)

### 3.3 Evaluation-Specific Testing
- **Structural checks**: feed deliberately-broken minutes (missing section, out-of-bounds source range, missing speaker) → verify all errors/warnings fire correctly
- **LLM-as-judge calibration**: run judge on a set of manually-scored sections → verify judge scores correlate with human scores (target: Pearson r > 0.7)
- **Judge-provider separation**: verify judge uses a different model/provider than generation (config check)
- **Score storage**: verify `generation_evals` populated after every generation
- **Feedback round-trip**: submit user feedback via API → verify stored in `section_feedback` → verify queryable for analysis
- **Style extraction**: upload example minutes → verify style profile JSON generated with all dimensions → regenerate with style → verify output reflects style delta
- **Regression detection**: run generation with previous prompt version → compare scores → verify regression alert triggers on score drop > 0.5

### 3.4 Multi-language Testing
- Test with mixed Mandarin/English board meeting transcript
- Verify minutes output in designated language
- Verify speaker attribution preserved across language boundaries
- Verify LLM-as-judge correctly evaluates non-English content

---

## 4. Open Questions

1. **Chat vs traditional UI**: Build the chat interface in Phase 6 or bring it forward? The user expressed interest in chat-based interaction. Architecture supports both (same API, different frontend shell).

2. **Transcription provider for SEA languages**: Deepgram vs Whisper accuracy for SEA languages (Thai, Vietnamese, Bahasa, etc.) — needs evaluation before committing to a provider. Preprocessing normalizes all audio to 16kHz mono, so format support shouldn't be a deciding factor.

3. **Meeting length extremes**: The plan handles 4-hour meetings with increased chunking. Any known scenarios exceeding 6 hours? This would need a multi-stage summarization approach. Large recordings also raise ffmpeg processing time and temp storage concerns — a 6-hour video may take minutes just to extract and normalize audio.
