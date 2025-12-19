from datetime import datetime, timedelta
from typing import List
from fastapi import FastAPI, HTTPException, Depends, status, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
import models
from schemas import (
    RequestCreate, RequestUpdate, RequestResponse,
    UserLogin, Token, TokenData, UserBase, UserCreate, UserResponse,
    CommentCreate, CommentResponse, StatisticsResponse
)

# ---------- JWT НАСТРОЙКИ ----------

SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI(
    title="API учета заявок на ремонт климатического оборудования",
    version="1.0",
    description="API для системы учета заявок на ремонт климатического оборудования",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- УТИЛИТЫ ДЛЯ JWT И РОЛЕЙ ----------

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Создать JWT токен"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def authenticate_user(login: str, password: str):
    """Аутентификация пользователя"""
    user = models.get_user_by_login(login)
    if not user:
        return None
    if user["password"] != password:
        return None
    return user

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserBase:
    """Получить текущего пользователя из токена"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        role: str = payload.get("role")
        fio: str = payload.get("fio")
        if user_id is None or role is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = models.get_user_by_id(user_id)
    if user is None:
        raise credentials_exception

    return UserBase(
        user_id=user["user_id"],
        fio=user["fio"],
        phone=user["phone"],
        login=user["login"],
        role=user["role"]
    )

def require_roles(*allowed_roles: str):
    """Декоратор для проверки ролей"""
    def role_checker(current_user: UserBase = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Доступ запрещен для роли {current_user.role}"
            )
        return current_user
    return role_checker

# ---------- АУТЕНТИФИКАЦИЯ ----------

@app.post("/token", response_model=Token, summary="Получить JWT токен")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Аутентификация пользователя и получение токена"""
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={
            "user_id": user["user_id"],
            "role": user["role"],
            "fio": user["fio"]
        }
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/me", response_model=UserBase, summary="Информация о текущем пользователе")
async def read_users_me(current_user: UserBase = Depends(get_current_user)):
    """Получить информацию о текущем пользователе"""
    return current_user

# ---------- РЕГИСТРАЦИЯ ----------

@app.post("/register", response_model=UserResponse, summary="Регистрация нового пользователя")
def register_user(data: UserCreate):
    """Регистрация нового пользователя"""
    allowed_roles = ["Менеджер", "Оператор", "Специалист", "Заказчик"]
    if data.role not in allowed_roles:
        raise HTTPException(
            status_code=400,
            detail=f"Недопустимая роль. Разрешены: {', '.join(allowed_roles)}"
        )

    if models.is_login_taken(data.login):
        raise HTTPException(
            status_code=400,
            detail="Пользователь с таким логином уже существует"
        )

    user_id = models.create_user(
        fio=data.fio,
        phone=data.phone,
        login=data.login,
        password=data.password,
        role=data.role
    )

    return {
        "user_id": user_id,
        "fio": data.fio,
        "phone": data.phone,
        "login": data.login,
        "role": data.role
    }

# ---------- ЗАЯВКИ ----------

@app.get("/requests", summary="Список всех заявок")
def list_requests(current_user: UserBase = Depends(get_current_user)):
    """Получить список заявок с учетом роли пользователя"""
    if current_user.role == "Заказчик":
        rows = models.get_requests_by_client(current_user.user_id)
    elif current_user.role == "Специалист":
        rows = models.get_requests_by_master(current_user.user_id)
    else:
        rows = models.get_all_requests()
    
    return [dict(row) for row in rows]

@app.get("/requests/{request_id}", response_model=RequestResponse, summary="Получить заявку по ID")
def get_request(request_id: int, current_user: UserBase = Depends(get_current_user)):
    """Получить информацию о конкретной заявке"""
    request_data = models.get_request_by_id(request_id)
    if not request_data:
        raise HTTPException(status_code=404, detail="Заявка не найдена")

    # Проверка прав доступа
    if current_user.role == "Заказчик" and request_data["client_id"] != current_user.user_id:
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    
    if current_user.role == "Специалист" and request_data.get("master_id") != current_user.user_id:
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    return request_data

@app.post("/requests", summary="Создать новую заявку")
def add_request(data: RequestCreate, current_user: UserBase = Depends(require_roles("Оператор", "Заказчик", "Менеджер"))):
    """Создать новую заявку на ремонт"""
    # Устанавливаем статус по умолчанию
    if not data.request_status:
        data.request_status = "Новая заявка"
    
    # Если создает заказчик, устанавливаем его как клиента
    if current_user.role == "Заказчик":
        data.client_id = current_user.user_id
    
    request_id = models.create_request(data.dict())
    return {"message": "Заявка создана", "request_id": request_id}

@app.put("/requests/{request_id}", summary="Изменить заявку")
def edit_request(
    request_id: int, 
    data: RequestUpdate, 
    current_user: UserBase = Depends(require_roles("Оператор", "Менеджер", "Специалист"))
):
    """Обновить информацию о заявке"""
    request_data = models.get_request_by_id(request_id)
    if not request_data:
        raise HTTPException(status_code=404, detail="Заявка не найдена")

    # Проверка прав доступа для специалиста
    if current_user.role == "Специалист" and request_data.get("master_id") != current_user.user_id:
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    # Оператор не может менять ответственного специалиста
    if current_user.role == "Оператор" and "master_id" in data.dict(exclude_unset=True):
        data.master_id = request_data.get("master_id")

    success = models.update_request(request_id, data.dict(exclude_unset=True))
    if not success:
        raise HTTPException(status_code=400, detail="Не удалось обновить заявку")
    
    return {"message": "Заявка обновлена"}

@app.delete("/requests/{request_id}", summary="Удалить заявку")
def remove_request(
    request_id: int, 
    current_user: UserBase = Depends(require_roles("Менеджер"))
):
    """Удалить заявку (только для менеджера)"""
    if not models.get_request_by_id(request_id):
        raise HTTPException(status_code=404, detail="Заявка не найдена")

    success = models.delete_request(request_id)
    if not success:
        raise HTTPException(status_code=400, detail="Не удалось удалить заявку")
    
    return {"message": "Заявка удалена"}

# ---------- КОММЕНТАРИИ ----------

@app.get("/requests/{request_id}/comments", response_model=List[CommentResponse], summary="Комментарии по заявке")
def get_comments(request_id: int, current_user: UserBase = Depends(get_current_user)):
    """Получить комментарии к заявке"""
    request_data = models.get_request_by_id(request_id)
    if not request_data:
        raise HTTPException(status_code=404, detail="Заявка не найдена")

    # Проверка прав доступа
    if current_user.role == "Заказчик" and request_data["client_id"] != current_user.user_id:
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    
    if current_user.role == "Специалист" and request_data.get("master_id") != current_user.user_id:
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    comments = models.get_comments_by_request(request_id)
    return comments

@app.post("/requests/{request_id}/comments", response_model=CommentResponse, summary="Добавить комментарий")
def add_comment(
    request_id: int, 
    data: CommentCreate, 
    current_user: UserBase = Depends(require_roles("Специалист", "Менеджер"))
):
    """Добавить комментарий к заявке"""
    request_data = models.get_request_by_id(request_id)
    if not request_data:
        raise HTTPException(status_code=404, detail="Заявка не найдена")

    # Проверка, что специалист работает над этой заявкой
    if current_user.role == "Специалист" and request_data.get("master_id") != current_user.user_id:
        raise HTTPException(status_code=403, detail="Вы не являетесь ответственным за эту заявку")

    comment_id = models.create_comment(
        message=data.message,
        master_id=current_user.user_id,
        request_id=request_id
    )

    return {
        "comment_id": comment_id,
        "message": data.message,
        "master_id": current_user.user_id,
        "request_id": request_id,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

# ---------- СТАТИСТИКА ----------

@app.get("/stats/completed-count", summary="Количество выполненных заявок")
def stats_completed_count(current_user: UserBase = Depends(require_roles("Менеджер"))):
    """Получить количество выполненных заявок"""
    cnt = models.get_completed_requests_count()
    return {"completed_requests_count": cnt}

@app.get("/stats/average-time", summary="Среднее время выполнения заявки")
def stats_average_time(current_user: UserBase = Depends(require_roles("Менеджер"))):
    """Получить среднее время выполнения заявки в днях"""
    avg_days = models.get_average_completion_time_days()
    return {"average_completion_time_days": avg_days}

@app.get("/stats/problems", summary="Статистика по типам неисправностей")
def stats_problems(current_user: UserBase = Depends(require_roles("Менеджер"))):
    """Получить статистику по типам неисправностей"""
    rows = models.get_problem_statistics()
    return rows

@app.get("/stats/all", summary="Вся статистика")
def all_stats(current_user: UserBase = Depends(require_roles("Менеджер"))):
    """Получить всю статистику"""
    return {
        "completed_requests_count": models.get_completed_requests_count(),
        "average_completion_time_days": models.get_average_completion_time_days(),
        "problem_statistics": models.get_problem_statistics()
    }

# ---------- ПОЛЬЗОВАТЕЛИ ----------

@app.get("/users/specialists", summary="Список всех специалистов")
def list_specialists(current_user: UserBase = Depends(require_roles("Оператор", "Менеджер"))):
    """Получить список всех специалистов"""
    specialists = models.get_all_specialists()
    return [{"user_id": s["user_id"], "fio": s["fio"], "phone": s["phone"]} for s in specialists]

@app.get("/users", summary="Список всех пользователей")
def list_users(current_user: UserBase = Depends(require_roles("Менеджер"))):
    """Получить список всех пользователей (только для менеджера)"""
    with models.get_db_cursor() as (cursor, _):
        cursor.execute("SELECT user_id, fio, phone, login, role FROM users ORDER BY role, fio")
        return [dict(row) for row in cursor.fetchall()]

# ---------- ЗАПУСК ПРИЛОЖЕНИЯ ----------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)