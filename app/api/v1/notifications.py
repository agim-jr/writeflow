from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def notifications():
    return {"message": "Notifications endpoint - coming soon"}
