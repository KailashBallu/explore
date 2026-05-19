# Meeting Intelligence

Meeting minutes generation tool for formal corporate meetings (board meetings, shareholder meetings, product announcements). Takes meeting recordings or transcripts as input and generates structured, legally-defensible minutes with full traceability — every generated point links back to its source in the transcript or recording.

## Documentation

- [Technical Design](./docs/technical-design.md) — Architecture, data model, API design, LangGraph workflow, frontend design
- [Development Plan](./docs/development-plan.md) — Phased development approach, verification plan, open questions

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.12 + FastAPI |
| **Agentic workflow** | LangGraph + LangChain |
| **Async tasks** | Celery + Redis |
| **Database** | PostgreSQL 16 |
| **Object storage** | S3-compatible (MinIO for dev) |
| **Transcription** | Deepgram / OpenAI Whisper |
| **LLM** | OpenAI GPT-4o (with provider abstraction) |
| **Frontend** | React 19 + Vite + TypeScript |
| **UI components** | shadcn/ui + Tailwind CSS |
| **Export** | python-docx + WeasyPrint (PDF) |

## Status

Planning — [design docs](./docs/) completed. Implementation pending.
