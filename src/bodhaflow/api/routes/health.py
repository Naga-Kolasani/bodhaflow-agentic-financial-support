from fastapi import APIRouter

router = APIRouter(tags=["System"])


@router.get("/health")
def get_health() -> dict[str, str]:
    return {"status": "ok"}
