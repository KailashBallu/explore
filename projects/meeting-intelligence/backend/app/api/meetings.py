from fastapi import APIRouter

router = APIRouter(prefix="/api/meetings", tags=["meetings"])


@router.get("/")
async def list_meetings():
    pass


@router.post("/")
async def create_meeting():
    pass


@router.get("/{meeting_id}")
async def get_meeting(meeting_id: str):
    pass


@router.put("/{meeting_id}")
async def update_meeting(meeting_id: str):
    pass


@router.delete("/{meeting_id}")
async def delete_meeting(meeting_id: str):
    pass
