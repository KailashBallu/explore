from fastapi import APIRouter

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
async def login() -> None:
    pass


@router.post("/refresh")
async def refresh() -> None:
    pass


@router.post("/logout")
async def logout() -> None:
    pass
