from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class RequestBase(BaseModel):
    start_date: str
    climate_tech_type: str
    climate_tech_model: str
    problem_description: str
    request_status: str
    master_id: Optional[int] = None
    client_id: int

class RequestCreate(RequestBase):
    pass

class RequestUpdate(BaseModel):
    request_status: Optional[str] = None
    problem_description: Optional[str] = None
    master_id: Optional[int] = None
    completion_date: Optional[str] = None
    repair_parts: Optional[str] = None

class RequestResponse(BaseModel):
    request_id: int
    start_date: str
    climate_tech_type: str
    climate_tech_model: str
    problem_description: str
    request_status: str
    completion_date: Optional[str] = None
    repair_parts: Optional[str] = None
    master_id: Optional[int] = None
    client_id: int

class UserLogin(BaseModel):
    login: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: int
    role: str
    fio: str

class UserBase(BaseModel):
    user_id: int
    fio: str
    phone: str
    login: str
    role: str

class UserCreate(BaseModel):
    fio: str
    phone: str
    login: str
    password: str
    role: str  # "Менеджер", "Оператор", "Специалист", "Заказчик"

class UserResponse(UserBase):
    pass

class CommentBase(BaseModel):
    message: str
    request_id: int

class CommentCreate(CommentBase):
    pass

class CommentResponse(CommentBase):
    comment_id: int
    master_id: int
    created_at: str

class StatisticsResponse(BaseModel):
    completed_requests_count: Optional[int] = None
    average_completion_time_days: Optional[float] = None
    problem_statistics: Optional[List[dict]] = None
    
