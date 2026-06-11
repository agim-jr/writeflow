from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any


class ExperimentBase(BaseModel):
    name: str
    description: Optional[str] = None
    experiment_type: str
    settings: Optional[Dict[str, Any]] = None


class ExperimentCreate(ExperimentBase):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class ExperimentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    results: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class ExperimentResponse(ExperimentBase):
    id: int
    user_id: int
    status: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    results: Optional[Dict[str, Any]] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
