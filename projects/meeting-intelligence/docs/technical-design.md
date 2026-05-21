# Meeting Intelligence — Technical Design Document

> **Version:** 1.3  
> **Date:** 2026-05-21  
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
- **Agenda** (optional) → used to structure/chunk the minutes. If not provided, the system auto-generates one via topic detection and prompts the user to review it before generation proceeds (or auto-approves, depending on user config).
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
| **Media preprocessing** | ffmpeg (libavcodec/libavformat) | Extract audio from video containers, normalize sample rate to 16kHz mono, transcode to provider-compatible format |
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
users (
  id, email, password_hash, display_name, default_language,
  settings JSONB,  -- user preferences: agenda_approval_mode, etc.
  created_at
)

meetings (
  id, user_id, name, meeting_type, date, location,
  language, agenda_text, agenda_approval_mode,  -- null = use user default; "always_review" | "auto_approve"
  status, created_at, updated_at
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
    agenda_items: list[AgendaItem] | None  # None = agenda not yet provided/generated
    attendees: list[dict]
    has_recording: bool
    recording_storage_key: str | None
    transcript_text: str | None

    # Agenda generation
    has_agenda: bool
    agenda_approval_mode: str  # "always_review" | "auto_approve"
    agenda_confidence_scores: dict[int, float]  # per-item confidence (1-5)
    agenda_review_approved: bool  # user confirmed in review_agenda node

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
          │ preprocess_media  │        │ process_transcript │
          │ (ffmpeg: extract  │        │ (parse + timestamp │
          │  audio, normalize │        │  detection)        │
          │  to 16kHz mono)   │        └────────┬──────────┘
          └────────┬─────────┘                  │
                   │                            │
                   ▼                            │
          ┌──────────────────┐                  │
          │   transcribe      │                  │
          │ (Deepgram/Whisper)│                  │
          └────────┬─────────┘                  │
                   │                            │
                   └───────────┬────────────────┘
                               ▼
                    ┌──────────────────┐
                    │   has_agenda?    │
                    └───┬──────────┬───┘
                        │ yes      │ no
                        ▼          ▼
                  ┌──────────┐  ┌─────────────────────┐
                  │ (skip)   │  │  generate_agenda     │
                  │          │  │  (LLM: topic detec-  │
                  │          │  │   tion, section      │
                  │          │  │   titles, confidence │
                  │          │  │   scores per item)   │
                  │          │  └──────────┬──────────┘
                  │          │             │
                  │          │             ▼
                  │          │  ┌─────────────────────┐
                  │          │  │  review_agenda       │
                  │          │  │  (interrupt() if     │
                  │          │  │   "always_review";   │
                  │          │  │   skip if "auto_     │
                  │          │  │   approve")          │
                  │          │  └──────────┬──────────┘
                  │          │             │
                  └──────────┼─────────────┘
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

**`validate_input`** — Deterministic. Checks required fields present, file uploads exist and are non-empty, transcript encoding valid. Sets initial `status` and `progress`. Determines `has_agenda` from input: true if user uploaded an agenda (at least one non-empty agenda item), false otherwise.

**`preprocess_media`** — Deterministic. Runs only when `has_recording` is true. Uses ffmpeg to normalize the uploaded recording into a consistent format before transcription. This node is the input-format boundary — everything downstream can assume a known audio format regardless of what the user uploaded.

Operations performed:
- **Video demuxing**: If the recording is a video container (`.mp4`, `.mov`, `.avi`, `.mkv`, `.webm`), extract the primary audio stream. Video track is discarded — no video features in v1.
- **Audio transcoding**: Transcode to 16kHz mono FLAC (lossless, widely accepted by both Deepgram and Whisper). Handles arbitrary input codecs (MP3, AAC, Opus, Vorbis, WMA, etc.).
- **Sample rate normalization**: Resample to 16kHz (both providers' recommended rate). Low sample rates (e.g., 8kHz conference recordings) get upsampled with appropriate filtering; high sample rates (44.1kHz, 48kHz) get downsampled.
- **Channel reduction**: Stereo/multi-channel → mono. In v1, diarization is handled entirely by the transcription provider, so channel-based speaker separation is not used.
- **Validation**: Detect silent/empty audio (output duration < 1s → error), verify output file is within provider size limits, report original and normalized durations.

ffmpeg runs as a subprocess; the normalized file is written to temp storage and cleaned up after transcription completes (or on failure). This node updates `state["recording_storage_key"]` to point to the normalized file.

**`transcribe`** — Calls transcription provider (Deepgram/Whisper) with the preprocessed, normalized audio file. Receives word-level timestamps + speaker diarization labels. Populates `transcript_segments`. On failure → retryable error.

**`process_transcript`** — Parses user-uploaded transcript. Detects timestamp patterns (`HH:MM:SS`, `[00:00]`, `<00:00:00>`). If timestamps found → populates `transcript_segments` with times. If not → creates segments by paragraph with no timestamps, sets `has_timestamps = False`.

**`generate_agenda`** — LLM node. Runs only when `has_agenda` is false (no user-provided agenda). This is a first-class, quality-rigorous node, not a fallback path.

Input: full `transcript_segments` list (or a windowed summary if transcript exceeds context window).

Output:
```python
{
    "items": [
        {
            "index": 0,
            "title": "1. Financial Review",
            "description": "Presentation and discussion of Q1 financial results",
            "confidence": 5,
            "boundary_segments": [0, 45],  # transcript segment indices for this topic
            "boundary_rationale": "Clear transition: chair introduces next agenda topic"
        },
        ...
    ],
    "overall_confidence": 4.2
}
```

LLM prompt design principles specific to this node:
- Topic boundary detection is the primary task — the LLM looks for explicit transitions (chair introductions, "next item", "moving on to"), speaker changes coinciding with topic shifts, time gaps in conversation, and semantic distance between adjacent transcript blocks
- Confidence scores (1–5) reflect how clear the boundary evidence is. High confidence means an unambiguous agenda-like transition phrase. Low confidence means the LLM guessed based on topic drift — these get visual warnings in the review UI
- Section titles follow formal minutes conventions ("Financial Review", not "They talked about money")
- Low-confidence items are still included — the user decides during review, not the LLM

**`review_agenda`** — Human-in-the-loop node. Behavior depends on `agenda_approval_mode`:

- `"always_review"` (default): calls `interrupt()` to yield control back to the frontend. The user sees the suggested agenda with confidence scores and can merge, split, rename, reorder, or delete items. The edited agenda is written into `state["agenda_items"]`. On resume, sets `agenda_review_approved = True`.

- `"auto_approve"`: skips the interrupt entirely. The generated agenda is accepted as-is. Sets `agenda_review_approved = True` and continues directly.

In both cases, when this node exits, `agenda_items` is guaranteed to be a non-empty list. This is the invariant downstream nodes rely on.

**`align_agenda`** — LLM node. **Precondition: `agenda_items` is always populated** (either user-provided or generated+reviewed). Maps each agenda item → relevant transcript segment indices. Segments not matching any agenda item go into "Other business." Uses structured JSON output.

**`summarize_agenda_item`** (fan-out via `Send()`) — One instance per agenda item, all in parallel. Each receives only its assigned transcript chunk. LLM generates: discussion summary, key points with speaker attribution, source segment references (character ranges + timestamps), in the specified output language.

**`extract_motions`** — LLM node. Extracts formal motions/resolutions: motion text, mover, seconder, voting result. Links to source segments.

**`extract_action_items`** — LLM node. Extracts action items: description, responsible person, deadline if mentioned. Links to source.

**`extract_next_meeting`** — LLM node. Extracts next meeting date/time/location if discussed.

**`assemble_minutes`** — Deterministic. Compiles all `generated_sections` (collected via `operator.add` reducer) into the final JSONB structure. Adds header and attendance sections from input metadata.

**`validate_minutes`** — Quality gate. Checks: all agenda items have summaries, source references within transcript bounds, speaker names populated (SEA requirement), no empty sections. When the agenda was auto-generated, also validates that confidence scores meet a minimum threshold on items flagged as "approved." If checks fail → conditional edge routes to repair node, then loops back.

### 6.5 Agenda Quality Evaluation

Agenda quality is evaluated separately because the agenda is the load-bearing structure for all downstream generation — if it's wrong, nothing downstream can recover.

**For auto-generated agendas (`generate_agenda` output):**

| Check | Severity | Description |
|-------|----------|-------------|
| Overall confidence >= 3.0 | WARNING | If overall confidence is low, flag the entire agenda for careful review |
| No single-item confidence = 1 | ERROR | A score of 1 means the LLM is guessing — reject the item, force the user to resolve it in review |
| All items have non-empty titles | ERROR | Empty titles cannot be aligned or summarized |
| Items collectively cover ≥85% of transcript | WARNING | Significant uncovered segments may indicate missed topics |
| No overlapping boundaries | ERROR | Overlap means the same transcript content maps to multiple items — ambiguous downstream |

**For user-provided agendas:**

| Check | Severity | Description |
|-------|----------|-------------|
| All items referenceable in transcript | WARNING | An agenda item that has no corresponding discussion in the transcript — may indicate the meeting skipped that topic |
| Agenda items ≥ 1 | ERROR | An empty agenda is not a valid input (user should use auto-generate instead) |

These checks run in `validate_input` (for user-provided agendas) and as a sub-check within `generate_agenda` (for auto-generated ones). Low-confidence items receive a visual warning badge in the review UI.

### 6.6 Progress Streaming

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

### 6.7 Checkpointing

LangGraph checkpoints state after each node execution via `PostgresSaver`. If the Celery worker crashes mid-pipeline, the workflow resumes from the last checkpoint.

### 6.8 LLM Prompt Design Principles
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

POST   /api/meetings/:id/agenda/suggest     # Trigger agenda generation from transcript
GET    /api/meetings/:id/agenda/suggest     # Get suggested agenda (with confidence scores)
PUT    /api/meetings/:id/agenda/suggest     # Submit edited agenda + approve, resume generation

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
3. Agenda:
   - **Paste agenda** (text or structured list) — the primary path for formal meetings
   - **Skip** — if no agenda is available, the system will auto-generate one from the transcript/recording. The agenda step shows:
     - A "Suggest from transcript" button (disabled until transcript/recording is uploaded)
     - A setting: **Approval mode** — "Always review suggested agenda" (default) or "Auto-approve and proceed." This can be pre-set at the user level and overridden per meeting.
     - A timeline note when recording is the input: "Your meeting will be transcribed first, then we'll suggest an agenda. With auto-approve, generation proceeds without waiting for you."
4. Upload recording and/or transcript
5. Confirm & start generation

When the user skips the agenda and uses "Suggest from transcript," the `generate_agenda` node produces a structured agenda with confidence scores per item. If approval mode is "always review," the wizard pauses after suggestion and shows the agenda for editing before proceeding to full generation.

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

## 9. Evaluation Framework

Quality evaluation is critical because the output is a legally-significant document. The evaluation system serves two audiences: developers (prompt engineering, regression testing) and end users (quality visibility, feedback loop).

### 9.1 Evaluation Dimensions

Each generated minutes section is scored on these dimensions:

| Dimension | Description | Measured By |
|-----------|-------------|-------------|
| **Accuracy** | Does the summary faithfully reflect the source transcript? No fabricated facts. | LLM-as-judge |
| **Completeness** | Are all key discussion points captured? No important omissions. | LLM-as-judge |
| **Speaker attribution** | Are points correctly attributed to the right speakers? (SEA requirement) | Deterministic + LLM-as-judge |
| **Structural validity** | Are all required sections present? Source links within bounds? | Deterministic |
| **Language quality** | Grammar, spelling, appropriate formality for minutes. | LLM-as-judge |
| **Conciseness** | Appropriate density — matches user's preferred level of detail. | LLM-as-judge (vs user preference) |

### 9.2 Automated Structural Checks (Deterministic)

These run as part of the `validate_minutes` node and after every generation. Always computed, zero LLM cost.

```
Check                                    | Severity
-----------------------------------------|----------
All agenda items have a summary section  | ERROR
Speaker name present on every point      | WARNING (SEA requirement)
Source character ranges within transcript bounds | ERROR
Source time ranges within recording duration     | ERROR
No empty/placeholder sections            | ERROR
Section ordinals are sequential          | WARNING
Attendance list matches input metadata   | WARNING
```

### 9.3 LLM-as-Judge (Automated)

A separate LLM call (different model or provider from generation) evaluates each section against the source transcript. This is the core automated quality metric.

**Approach**: Provide the judge LLM with:
1. The original transcript segment (source of truth)
2. The generated summary/motion/action item
3. A scoring rubric with 1–5 scale per dimension

**Judge prompt structure**:
```
You are evaluating the quality of meeting minutes generated from a transcript.

Source transcript segment:
---
{transcript_chunk}
---

Generated minutes section:
---
{generated_section}
---

Score each dimension 1-5 (1=poor, 5=excellent):

1. Accuracy: Does the summary faithfully reflect the source? No hallucinations?
2. Completeness: Are all key points from the source captured?
3. Speaker attribution: Are points attributed to the correct speakers?
4. Language quality: Grammar, spelling, appropriate formality?

For each score, provide a brief justification and the specific source text
that supports or contradicts the generated text.
```

**Why a separate LLM**: Using the same model to generate and evaluate risks self-confirmation bias. The judge should be a different model or at minimum a separate, zero-temperature call.

**Cost**: Per 2-hour meeting (~7 agenda items): ~8 judge calls (one per agenda item + motions + actions). Approximately 15–20k additional tokens per meeting.

### 9.4 Development Evaluation Loop

During prompt engineering and model evaluation:
1. Generate minutes for a test meeting → get scores
2. Change prompt/model → generate again → compare scores
3. Track score trends over time (stored in DB alongside each generation)
4. Flag regressions: if any dimension drops >0.5 points, alert the developer

This makes prompt iteration data-driven rather than subjective.

### 9.5 User-Facing Quality Scores

Each section in the review editor shows a quality indicator:

```
┌─────────────────────────────────────────┐
│ 1. Financial Review          Accuracy ●●●●○ 4.2  │
│    Mr. Tan presented the Q1  Completeness ●●●●○ 3.8 │
│    financial results...      Attribution ●●●●● 5.0  │
│                              [flag for review]       │
└─────────────────────────────────────────┘
```

- Scores shown as 1–5 dots with numeric value
- Sections scoring below threshold (e.g., <3.5) are highlighted in yellow
- Users can click "flag for review" on any section regardless of score
- Aggregate meeting-level score shown in dashboard

### 9.6 User Feedback Collection

Embedded in the review editor:
- **Per-section**: thumbs up/down, flag for review, free-text note
- **Per-meeting**: overall satisfaction rating, free-text feedback
- **Post-export**: optional NPS-style question ("How much editing was needed?")

This feedback data is stored and used to:
- Identify systematic issues (e.g., a prompt that consistently misses action items)
- Calibrate the LLM-as-judge scores against real user satisfaction
- Prioritize improvements

### 9.7 Style Customization via User Samples

Users can upload example minutes they've written or approved to customize output style. This addresses the fact that different organizations prefer different levels of detail.

**How it works**:
1. User uploads 1–3 example minutes documents they consider "gold standard"
2. System extracts style characteristics via LLM analysis:
   - Conciseness: average words per agenda item
   - Formality level: vocabulary, sentence structure
   - Detail density: are motions described in detail or summarized?
   - Structural preferences: section ordering, heading style
3. A style profile (JSON) is stored on the user record
4. The `summarize_agenda_item` node receives the style profile as part of its prompt:

```
Style preferences for this organization:
- Conciseness: concise (prefer bullet points over paragraphs)
- Formality: high (use formal board-meeting language)
- Detail: motions should include full voting breakdowns
```

**Why not few-shot prompting directly**: Few-shot with full example minutes would blow the context window. Extracting a style profile is token-efficient and reusable across all future generations.

### 9.8 Data Model Additions

```sql
-- Per-generation evaluation scores
generation_evals (
  id, meeting_id, minutes_id, section_id, eval_method,  -- eval_method: structural | llm_judge | user
  accuracy_score, completeness_score, attribution_score,
  language_score, conciseness_score,
  judge_model, judge_raw_response, created_at
)

-- User feedback on generated content
section_feedback (
  id, section_id, user_id, rating,  -- rating: thumbs_up | thumbs_down | flag
  free_text, created_at
)

-- User style profile
user_style_profiles (
  id, user_id, style_config (JSONB),
  source_minutes_ids, created_at, updated_at
)
```

### 9.9 API Additions

```
GET    /api/meetings/:id/minutes/:vid/evaluation    # Get quality scores for all sections
POST   /api/meetings/:id/minutes/:vid/sections/:sid/feedback  # Submit user feedback
GET    /api/users/me/style-profile                  # Get current style profile
POST   /api/users/me/style-profile/samples          # Upload example minutes for style extraction
```

---

## 10. Key Decisions

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
