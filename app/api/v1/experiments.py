from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def experiments():
    return {"message": "Experiments endpoint - coming soon"}
