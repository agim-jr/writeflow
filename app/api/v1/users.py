from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_users():
    return {"message": "Users endpoint - coming soon"}
