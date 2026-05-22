import operator
from typing import Annotated, TypedDict


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
    agenda_items: list[AgendaItem] | None
    attendees: list[dict]
    has_recording: bool
    recording_storage_key: str | None
    transcript_text: str | None

    # Agenda generation
    has_agenda: bool
    agenda_approval_mode: str
    agenda_confidence_scores: dict[int, float]
    agenda_review_approved: bool

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
