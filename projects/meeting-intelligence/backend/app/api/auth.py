from fastapi import APIRouter

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
async def login():
    pass


@router.post("/refresh")
async def refresh():
    pass


@router.post("/logout")
async def logout():
    pass
