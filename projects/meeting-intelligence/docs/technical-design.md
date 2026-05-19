# Meeting Intelligence — Technical Design Document

> **Version:** 1.0  
> **Date:** 2026-05-18  
> **Status:** Planning

---

## 1. Context

Meeting Intelligence is a meeting minutes generation tool for companies. The primary use case is formal meetings (board meetings, shareholder meetings, product announcements) where minutes must be accurate, well-structured, and legally defensible. The tool takes meeting recordings or transcripts as input, generates structured minutes, and provides an in-app review experience where every generated point links back to its source in the transcript/recording.

**Key differentiator: traceability** — click any generated minute point to jump to the relevant transcript segment or replay the recording from that moment.

---

## 2. Requirements Summary

### 2.1 Users
- Corporate secretaries and executive assistants
- Single-user, single-role (no multi-tenancy in v1)
- Companies globally, especially South-east Asia

### 2.2 Input
- **Recording** (audio/video) → tool invokes transcription with timestamps and speaker diarization
- **Transcript** (text, timestamps optional) → user-provided; when timestamps missing, replay feature is disabled
- **Agenda** → used to structure/chunk the minutes
- **Meeting metadata** → name, date/time, location/virtual, attendees list

### 2.3 Output
- Structured minutes with components: header, attendance, agenda items with discussion summaries, motions/resolutions, action items, attachments, next meeting info
- Every generated point links to source transcript segment + recording timestamp (when available)
- Editable in-app with side-by-side source view
- Export (DOCX/PDF)

### 2.4 Language
- Multi-language: original speaker languages preserved in transcript, minutes generated in a designated language
- Multiple languages may appear in the same meeting

### 2.5 Legal Compliance
- **SEA requirement**: record which speaker expressed which point/opinion (speaker attribution on every generated point)
- Design extensibility for other jurisdiction requirements (US, UK, EU, etc.)

### 2.6 Data Retention & Hosting
- Recordings and transcripts auto-deleted after 30 days (configurable)
- Cloud-deployable, provider-agnostic (recommend AWS/GCP/Azure)
- Third-party LLM API (OpenAI initially), with provider abstraction

### 2.7 Out of Scope (v1)
- Electronic signing workflow
- Calendar/video-conferencing integrations
- Multi-tenant organization management
- Self-hosted LLM

---

## 3. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React SPA)                       │
│  ┌──────────┐  ┌──────────────┐  ┌─────────────────────────┐ │
│  │ Dashboard │  │ Upload Flow  │  │ Review Editor           │ │
│  │ (meeting  │  │ (metadata +  │  │ (side-by-side: minutes  │ │
│  │  history) │  │  files)      │  │  + transcript/recording)│ │
│  └──────────┘  └──────────────┘  └─────────────────────────┘ │
└──────────────────────┬──────────────────────────────────────┘
                       │ REST API + WebSocket (streaming progress)
┌──────────────────────▼──────────────────────────────────────┐
│                  Backend (Python / FastAPI)                   │
│                                                               │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐  │
│  │ API Layer   │  │ Task Queue   │  │ Provider Layer     │  │
│  │ (auth, CRUD,│  │ (Celery      │  │ (LLM: OpenAI/GPT  │  │
│  │  file mgmt) │  │  dispatches   │  │  Transcription:    │  │
│  └──────┬──────┘  │  LangGraph    │  │  Whisper/Deepgram) │  │
│         │         │  workflows)   │  └─────────┬──────────┘  │
│         │         └──────┬───────┘            │              │
│         │                │                    │              │
│         │    ┌───────────▼────────────────────▼──────────┐  │
│         │    │        LangGraph Workflow                  │  │
│         │    │  (Minutes Generation StateGraph)           │  │
│         │    │                                            │  │
│         │    │  ┌──────────┐  ┌──────────────────────┐   │  │
│         │    │  │Validate  │─▶│ Transcribe (if rec.) │   │  │
│         │    │  │Input     │  └──────────┬───────────┘   │  │
│         │    │  └──────────┘             │               │  │
│         │    │                           ▼               │  │
│         │    │  ┌────────────────────────────────────┐   │  │
│         │    │  │      Agenda-Transcript Align       │   │  │
│         │    │  └────────────────┬───────────────────┘   │  │
│         │    │                   │                        │  │
│         │    │      ┌────────────┼────────────┐          │  │
│         │    │      │            │            │          │  │
│         │    │      ▼            ▼            ▼          │  │
│         │    │  ┌────────┐ ┌──────────┐ ┌──────────┐    │  │
│         │    │  │Agenda  │ │Extract   │ │Extract   │    │  │
│         │    │  │Item 1..N│ │Motions   │ │Actions   │    │  │
│         │    │  │(parallel│ │          │ │          │    │  │
│         │    │  │via Send)│ │          │ │          │    │  │
│         │    │  └───┬────┘ └────┬─────┘ └────┬─────┘    │  │
│         │    │      │           │            │           │  │
│         │    │      └───────────┼────────────┘           │  │
│         │    │                  ▼                        │  │
│         │    │  ┌────────────────────────────────────┐   │  │
│         │    │  │  Validate & Assemble Minutes       │   │  │
│         │    │  │  (quality check, completeness)     │   │  │
│         │    │  └────────────────────────────────────┘   │  │
│         │    └──────────────────────────────────────────┘  │
│         │                                                  │
└─────────┼──────────────────────────────────────────────────┘
          │
┌─────────▼──────────────────────────────────────────────────┐
│                    Data Layer                                │
│  ┌──────────────┐  ┌──────────────────┐  ┌───────────────┐  │
│  │ PostgreSQL    │  │ Object Storage   │  │ Redis          │  │
│  │ (metadata,    │  │ (recordings,     │  │ (Celery broker,│  │
│  │  minutes,     │  │  transcripts,    │  │  progress pub/ │  │
│  │  checkpoints) │  │  exports)        │  │  sub, cache)   │  │
│  └──────────────┘  └──────────────────┘  └───────────────┘  │
│  Object storage has lifecycle policy: delete files after 30d │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Tech Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Backend** | Python 3.12 + FastAPI | Async, good file upload handling, OpenAPI docs |
| **Agentic workflow** | LangGraph + LangChain | Stateful multi-step graph, fan-out parallelism, checkpointing, human-in-the-loop |
| **Async tasks** | Celery + Redis | Runs LangGraph workflows in background; Redis as broker + progress pub/sub |
| **Database** | PostgreSQL 16 | JSONB for minutes structure, full-text search; LangGraph checkpoint storage |
| **Object storage** | S3-compatible (MinIO for local dev) | Lifecycle policies for 30-day auto-delete |
| **Transcription** | Deepgram (primary) or OpenAI Whisper | Both provide word-level timestamps + diarization |
| **LLM** | OpenAI GPT-4o (initial), with provider abstraction | Structured output via JSON mode / function calling |
| **Frontend** | React 19 + Vite + TypeScript | Fast dev, typed |
| **UI components** | shadcn/ui + Tailwind CSS | Clean, customizable |
| **Frontend state** | TanStack Query + Zustand | Server state + local state |
| **Export** | python-docx + WeasyPrint (PDF) | Generate DOCX and PDF from structured minutes |
| **Auth** | JWT (access + refresh tokens) | Simple, stateless, single-user v1 |
| **Container** | Docker + docker-compose (dev), k8s manifest (prod) | Reproducible deployment |
| **CI/CD** | GitHub Actions | Test, lint, build |

### 4.1 Provider Abstraction (LLM)

```python
# Simple interface, implement per provider
class LLMProvider(Protocol):
    async def chat_completion(self, messages: list, schema: dict | None) -> dict: ...
    async def streaming_completion(self, messages: list) -> AsyncIterator[str]: ...

class OpenAIProvider(LLMProvider): ...
class AnthropicProvider(LLMProvider): ...  # future
class AzureProvider(LLMProvider): ...     # future
```

Provider is selected via config/env var. Single-file swap. Minimal cost (~50 lines of interface code).

---

## 5. Data Model

### 5.1 SQL Schema

```sql
-- Core tables
users (id, email, password_hash, display_name, default_language, created_at)

meetings (
  id, user_id, name, meeting_type, date, location,
  language, agenda_text, status, created_at, updated_at
)
-- status: draft | processing | ready_review | signed | archived

meeting_attendees (id, meeting_id, name, role, present boolean)

meeting_files (
  id, meeting_id, file_type, storage_key, original_filename,
  mime_type, duration_seconds, has_timestamps, language, expires_at
)
-- file_type: recording | transcript | attachment

minutes (
  id, meeting_id, version, status, content (JSONB),
  created_at, updated_at
)

minutes_sections (
  id, minutes_id, section_type, ordinal, heading,
  body_html, body_json, source_start_char, source_end_char,
  source_start_time, source_end_time, speaker_name,
  created_at
)
-- section_type: header | attendance | agenda_item | motion | action_item | next_meeting
-- source_* columns provide traceability back to transcript/recording
-- speaker_name addresses the SEA legal requirement

action_items (id, meeting_id, meeting_attendee_id, description, due_date, status)
```

### 5.2 Minutes JSONB Structure

```json
{
  "title": "Board Meeting — Acme Corp Q2 2026",
  "sections": [
    {
      "type": "header",
      "content": { "date": "...", "time": "...", "location": "...", "type": "..." }
    },
    {
      "type": "attendance",
      "content": { "present": ["..."], "absent": ["..."], "guests": ["..."], "quorum": true }
    },
    {
      "type": "agenda_item",
      "agenda_ref": "1. Financial Review",
      "discussion_summary": "<p>Mr. Tan presented the Q1 financial results...</p>",
      "speakers": ["Mr. Tan", "Ms. Lee"],
      "source_segments": [
        { "transcript_range": [1200, 1850], "time_range": ["00:20:00", "00:30:50"], "speaker": "Mr. Tan" }
      ]
    },
    {
      "type": "motion",
      "content": {
        "motion_text": "Approve the Q1 financial statements as presented.",
        "moved_by": "Mr. Tan",
        "seconded_by": "Ms. Lee",
        "votes": { "for": 7, "against": 0, "abstain": 1 },
        "result": "passed"
      },
      "source_segments": [...]
    }
  ]
}
```

The `source_segments` array is the core of the traceability feature. Each entry maps a generated minute point back to character offsets in the transcript and time offsets in the recording.

---

## 6. LangGraph Agentic Workflow

### 6.1 Why LangGraph

| Concern | Celery chain/canvas | LangGraph |
|---------|---------------------|-----------|
| Fan-out parallelism per agenda item | Awkward — need chord/groups with dynamic count | Native via `Send()` API |
| State passing between steps | Pass through result backends | Typed `State` object, all nodes read/write it |
| Conditional branching (recording vs transcript) | Chain with immutable steps | Conditional edges |
| Progress streaming to frontend | Manual Redis pub/sub | Built-in `astream_events()` + custom callbacks |
| Durability / crash recovery | Celery retry on task failure | LangGraph checkpointing (persist to PostgreSQL) |
| Human-in-the-loop (review → retry) | Not supported | `interrupt()` / `Command()` built-in |
| Validation-retry loops (quality gate) | Manual retry logic | Conditional edge back to generating node |

### 6.2 State Definition

```python
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.constants import Send
import operator

class TranscriptSegment(TypedDict):
    text: str
    start_char: int
    end_char: int
    start_time: str | None
    end_time: str | None
    speaker: str | None

class AgendaItem(TypedDict):
    index: int
    title: str
    description: str

class GeneratedSection(TypedDict):
    type: str
    ordinal: int
    heading: str
    body_html: str
    body_json: dict
    source_segments: list[dict]
    speaker_name: str | None

class MinutesState(TypedDict):
    # Input
    meeting_id: str
    meeting_name: str
    meeting_date: str
    meeting_location: str
    meeting_type: str
    output_language: str
    agenda_items: list[AgendaItem]
    attendees: list[dict]
    has_recording: bool
    recording_storage_key: str | None
    transcript_text: str | None

    # Intermediate
    transcript_segments: list[TranscriptSegment]
    has_timestamps: bool
    agenda_alignment: dict
    generated_sections: Annotated[list[GeneratedSection], operator.add]

    # Output
    assembled_minutes: dict | None
    validation_errors: list[str]

    # Control
    status: str
    progress: float
    progress_message: str
```

### 6.3 Graph Topology

```
                         ┌─────────────────┐
                         │  validate_input  │
                         └────────┬────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    │ has_recording?              │ no recording
                    ▼                             ▼
          ┌──────────────────┐        ┌───────────────────┐
          │   transcribe      │        │ process_transcript │
          │ (Deepgram/Whisper)│        │ (parse + timestamp │
          └────────┬─────────┘        │  detection)        │
                   │                  └────────┬──────────┘
                   │                           │
                   └───────────┬───────────────┘
                               ▼
                    ┌──────────────────┐
                    │  align_agenda    │
                    │ (LLM: map agenda │
                    │  items → segments)│
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────────┐
              │ Send()       │                  │ Send()
              ▼              ▼                  ▼
   ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐
   │summarize_item│ │summarize_item│ │summarize_item... │
   │(agenda[0])   │ │(agenda[1])   │ │(agenda[N])       │
   └──────┬───────┘ └──────┬───────┘ └────────┬─────────┘
          │                │                  │
          └────────────────┼──────────────────┘
                           │ (all items complete)
                           ▼
              ┌────────────────────────┐
              │  extract_motions       │
              │  extract_action_items  │
              │  extract_next_meeting  │
              └───────────┬────────────┘
                          │
                          ▼
              ┌────────────────────────┐
              │  assemble_minutes      │
              └───────────┬────────────┘
                          │
                          ▼
              ┌────────────────────────┐
              │  validate_minutes      │
              └───────────┬────────────┘
                    ┌─────┴─────┐
                    │ pass?     │ fail?
                    ▼           ▼
                   END    ┌──────────────┐
                          │ repair_*      │
                          │ (conditional  │
                          │  edge back to │
                          │  failing node)│
                          └──────────────┘
```

### 6.4 Node Details

**`validate_input`** — Deterministic. Checks required fields present, recording format supported, transcript encoding valid. Sets initial `status` and `progress`.

**`transcribe`** — Calls transcription provider (Deepgram/Whisper). Receives word-level timestamps + speaker diarization labels. Populates `transcript_segments`. On failure → retryable error.

**`process_transcript`** — Parses user-uploaded transcript. Detects timestamp patterns (`HH:MM:SS`, `[00:00]`, `<00:00:00>`). If timestamps found → populates `transcript_segments` with times. If not → creates segments by paragraph with no timestamps, sets `has_timestamps = False`.

**`align_agenda`** — LLM node. Maps each agenda item → relevant transcript segment indices. Segments not matching any agenda item go into "Other business." If no agenda provided, chunks by topic transitions. Uses structured JSON output.

**`summarize_agenda_item`** (fan-out via `Send()`) — One instance per agenda item, all in parallel. Each receives only its assigned transcript chunk. LLM generates: discussion summary, key points with speaker attribution, source segment references (character ranges + timestamps), in the specified output language.

**`extract_motions`** — LLM node. Extracts formal motions/resolutions: motion text, mover, seconder, voting result. Links to source segments.

**`extract_action_items`** — LLM node. Extracts action items: description, responsible person, deadline if mentioned. Links to source.

**`extract_next_meeting`** — LLM node. Extracts next meeting date/time/location if discussed.

**`assemble_minutes`** — Deterministic. Compiles all `generated_sections` (collected via `operator.add` reducer) into the final JSONB structure. Adds header and attendance sections from input metadata.

**`validate_minutes`** — Quality gate. Checks: all agenda items have summaries, source references within transcript bounds, speaker names populated (SEA requirement), no empty sections. If checks fail → conditional edge routes to repair node, then loops back.

### 6.5 Progress Streaming

LangGraph's `astream_events()` streams node transitions via Redis pub/sub → WebSocket:

```python
async for event in graph.astream_events(initial_state, version="v2"):
    if event["event"] == "on_custom_event" and event["name"] == "progress":
        redis.publish(f"meeting:{meeting_id}:progress", json.dumps({
            "status": event["data"]["status"],
            "progress": event["data"]["progress"],
            "message": event["data"]["message"]
        }))
```

### 6.6 Checkpointing

LangGraph checkpoints state after each node execution via `PostgresSaver`. If the Celery worker crashes mid-pipeline, the workflow resumes from the last checkpoint.

### 6.7 LLM Prompt Design Principles
- **Structured output**: Every LLM node uses JSON mode / function calling
- **Source linking**: LLM returns character ranges in the transcript supporting each statement (citation-style)
- **Speaker attribution**: From diarization labels + LLM inference; required by SEA jurisdictions
- **Language instruction**: System prompt specifies output language; transcript segments in original languages
- **Token-efficient**: Agenda items get only their relevant transcript chunk, not the full transcript

---

## 7. API Design

```
POST   /api/auth/login, /api/auth/refresh, /api/auth/logout

GET    /api/meetings                        # List user's meetings
POST   /api/meetings                        # Create meeting with metadata
GET    /api/meetings/:id                    # Meeting detail
PUT    /api/meetings/:id                    # Update metadata
DELETE /api/meetings/:id                    # Delete meeting + files

POST   /api/meetings/:id/upload             # Upload recording/transcript/attachment
WS     /api/meetings/:id/status             # Stream processing status

POST   /api/meetings/:id/generate           # Trigger minutes generation
GET    /api/meetings/:id/minutes/latest     # Get latest minutes
PUT    /api/meetings/:id/minutes/:vid       # Update edited minutes content
GET    /api/meetings/:id/minutes/:vid/sections/:sid/source  # Get source transcript segment

POST   /api/meetings/:id/export             # Export as DOCX or PDF
GET    /api/meetings/:id/export/:job_id     # Check export status, download when ready
```

---

## 8. Frontend Design

### 8.1 Navigation
```
Dashboard → Meeting List → Upload Flow → Minutes Review Editor → Export
```

### 8.2 Key Screens

**Dashboard** — List of meetings with status badges (processing, ready for review, signed). Quick actions: New Meeting, Continue Review.

**Upload Flow** — Step-by-step wizard:
1. Meeting metadata (name, date, type, language, location)
2. Attendees (add names + roles, mark present/absent)
3. Agenda (paste text or structured list)
4. Upload recording and/or transcript
5. Confirm & start generation

**Review Editor** — The core experience:
```
┌────────────────────────────┬──────────────────────────────┐
│     Minutes (editable)     │   Source Transcript/Player   │
│  ┌──────────────────────┐  │  ┌────────────────────────┐  │
│  │ Header               │  │  │ [Audio Player]         │  │
│  │ ✓ Attendance          │  │  │                        │  │
│  │                        │  │  │ 00:20:00 Mr. Tan:     │  │
│  │ 1. Financial Review   │◄─│──┤ The Q1 financial       │  │
│  │    Mr. Tan presented  │  │  │ results show a 12%     │  │
│  │    the Q1 results...  │  │  │ increase in revenue... │  │
│  │                        │  │  │                        │  │
│  │ Motion: Approve Q1    │  │  │ 00:32:15 Ms. Lee:      │  │
│  │ statements...         │  │  │ I second the motion... │  │
│  └──────────────────────┘  │  └────────────────────────┘  │
└────────────────────────────┴──────────────────────────────┘
```
- Hovering a minute point highlights the corresponding transcript segment
- Clicking plays the recording from that timestamp (if available)
- Editable rich-text fields, sections can be reordered
- Version history (auto-save drafts)

### 8.3 Chat-Based UI (Future)
A chat interface can serve as an alternative to the upload wizard and as a review assistant. It would use the same backend API with an LLM-powered chat layer that converts natural language instructions into API calls.

**Recommendation**: Build the traditional UI first. The chat interface is additive.

---

## 9. Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Agentic workflow engine | LangGraph StateGraph | Fan-out parallelism, typed state, checkpointing, human-in-the-loop |
| Async execution | Celery dispatches LangGraph | Don't block web server; Celery retry/durability; LangGraph orchestration |
| Transcript timestamps | Accept both; disable replay when missing | Don't block users with their own transcripts |
| Transcription service | Deepgram primary (Whisper fallback) | Deepgram has better diarization |
| LLM provider abstraction | Build now | ~50 lines of interface; trivial cost, high future value |
| Minutes storage | JSONB in PostgreSQL | Queryable, versionable |
| Checkpoint storage | PostgreSQL (PostgresSaver) | Reuse existing DB |
| 30-day deletion | S3 lifecycle policies | Automatic, reliable |
| Frontend approach | Traditional UI first, chat later | Core review experience needs rich editor |
| Speaker attribution | Diarization labels + LLM inference | Required by SEA jurisdictions |
