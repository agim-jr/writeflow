from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def ai_insights():
    return {"message": "AI Insights endpoint - coming soon"}
