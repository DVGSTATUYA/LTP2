import sqlite3
from typing import List, Optional, Dict, Any
from contextlib import contextmanager
from datetime import datetime

DATABASE_PATH = "repair_requests.db"

@contextmanager
def get_db_connection():
    """Контекстный менеджер для соединения с БД"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

@contextmanager
def get_db_cursor():
    """Контекстный менеджер для работы с курсором БД"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            yield cursor, conn
        finally:
            cursor.close()

# ---------- ПОЛЬЗОВАТЕЛИ ----------

def get_user_by_login(login: str) -> Optional[Dict]:
    """Получить пользователя по логину"""
    with get_db_cursor() as (cursor, _):
        cursor.execute("SELECT * FROM users WHERE login = ?", (login,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_user_by_id(user_id: int) -> Optional[Dict]:
    """Получить пользователя по ID"""
    with get_db_cursor() as (cursor, _):
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def create_user(fio: str, phone: str, login: str, password: str, role: str) -> int:
    """Создать нового пользователя"""
    with get_db_cursor() as (cursor, conn):
        cursor.execute("""
            INSERT INTO users (fio, phone, login, password, role)
            VALUES (?, ?, ?, ?, ?)
        """, (fio, phone, login, password, role))
        conn.commit()
        return cursor.lastrowid

def is_login_taken(login: str) -> bool:
    """Проверить, занят ли логин"""
    with get_db_cursor() as (cursor, _):
        cursor.execute("SELECT COUNT(*) as count FROM users WHERE login = ?", (login,))
        result = cursor.fetchone()
        return result["count"] > 0

# ---------- ЗАЯВКИ ----------

def get_all_requests() -> List[Dict]:
    """Получить все заявки"""
    with get_db_cursor() as (cursor, _):
        cursor.execute("SELECT * FROM requests ORDER BY start_date DESC")
        return [dict(row) for row in cursor.fetchall()]

def get_request_by_id(request_id: int) -> Optional[Dict]:
    """Получить заявку по ID"""
    with get_db_cursor() as (cursor, _):
        cursor.execute("SELECT * FROM requests WHERE request_id = ?", (request_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def create_request(request_data: Dict) -> int:
    """Создать новую заявку"""
    with get_db_cursor() as (cursor, conn):
        cursor.execute("""
            INSERT INTO requests (
                start_date, climate_tech_type, climate_tech_model,
                problem_description, request_status, master_id, client_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            request_data["start_date"],
            request_data["climate_tech_type"],
            request_data["climate_tech_model"],
            request_data["problem_description"],
            request_data["request_status"],
            request_data.get("master_id"),
            request_data["client_id"]
        ))
        conn.commit()
        return cursor.lastrowid

def update_request(request_id: int, update_data: Dict) -> bool:
    """Обновить заявку"""
    with get_db_cursor() as (cursor, conn):
        # Собираем поля для обновления
        fields = []
        values = []
        
        if "request_status" in update_data and update_data["request_status"]:
            fields.append("request_status = ?")
            values.append(update_data["request_status"])
        
        if "problem_description" in update_data and update_data["problem_description"]:
            fields.append("problem_description = ?")
            values.append(update_data["problem_description"])
        
        if "master_id" in update_data:
            fields.append("master_id = ?")
            values.append(update_data["master_id"])
        
        if "completion_date" in update_data and update_data["completion_date"]:
            fields.append("completion_date = ?")
            values.append(update_data["completion_date"])
        
        if "repair_parts" in update_data:
            fields.append("repair_parts = ?")
            values.append(update_data["repair_parts"])
        
        if not fields:
            return False
        
        values.append(request_id)
        query = f"UPDATE requests SET {', '.join(fields)} WHERE request_id = ?"
        cursor.execute(query, values)
        conn.commit()
        return cursor.rowcount > 0

def delete_request(request_id: int) -> bool:
    """Удалить заявку"""
    with get_db_cursor() as (cursor, conn):
        cursor.execute("DELETE FROM requests WHERE request_id = ?", (request_id,))
        conn.commit()
        return cursor.rowcount > 0

def get_requests_by_client(client_id: int) -> List[Dict]:
    """Получить заявки клиента"""
    with get_db_cursor() as (cursor, _):
        cursor.execute("SELECT * FROM requests WHERE client_id = ? ORDER BY start_date DESC", (client_id,))
        return [dict(row) for row in cursor.fetchall()]

def get_requests_by_master(master_id: int) -> List[Dict]:
    """Получить заявки мастера"""
    with get_db_cursor() as (cursor, _):
        cursor.execute("SELECT * FROM requests WHERE master_id = ? ORDER BY start_date DESC", (master_id,))
        return [dict(row) for row in cursor.fetchall()]



# ---------- КОММЕНТАРИИ ----------

def get_comments_by_request(request_id: int) -> List[Dict]:
    """Получить комментарии по заявке"""
    with get_db_cursor() as (cursor, _):
        cursor.execute("""
            SELECT c.*, u.fio as master_name 
            FROM comments c
            LEFT JOIN users u ON c.master_id = u.user_id
            WHERE c.request_id = ?
            ORDER BY c.created_at DESC
        """, (request_id,))
        return [dict(row) for row in cursor.fetchall()]

def create_comment(message: str, master_id: int, request_id: int) -> int:
    """Создать комментарий"""
    with get_db_cursor() as (cursor, conn):
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO comments (message, master_id, request_id, created_at)
            VALUES (?, ?, ?, ?)
        """, (message, master_id, request_id, created_at))
        conn.commit()
        return cursor.lastrowid

# ---------- СТАТИСТИКА ----------

def get_completed_requests_count() -> int:
    """Получить количество выполненных заявок"""
    with get_db_cursor() as (cursor, _):
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM requests 
            WHERE request_status IN ('Готова к выдаче', 'Завершена')
        """)
        result = cursor.fetchone()
        return result["count"]

def get_average_completion_time_days() -> Optional[float]:
    """Получить среднее время выполнения заявки в днях"""
    with get_db_cursor() as (cursor, _):
        cursor.execute("""
            SELECT 
                AVG(
                    julianday(completion_date) - julianday(start_date)
                ) as avg_days
            FROM requests 
            WHERE completion_date IS NOT NULL 
            AND completion_date != ''
        """)
        result = cursor.fetchone()
        return result["avg_days"] if result["avg_days"] else None

def get_problem_statistics() -> List[Dict]:
    """Получить статистику по типам неисправностей"""
    with get_db_cursor() as (cursor, _):
        cursor.execute("""
            SELECT 
                problem_description as problem_type,
                COUNT(*) as cnt
            FROM requests 
            GROUP BY problem_description
            ORDER BY cnt DESC
        """)
        return [dict(row) for row in cursor.fetchall()]

def get_users_by_role(role: str) -> List[Dict]:
    """Получить пользователей по роли"""
    with get_db_cursor() as (cursor, _):
        cursor.execute("SELECT * FROM users WHERE role = ?", (role,))
        return [dict(row) for row in cursor.fetchall()]

def get_all_specialists() -> List[Dict]:
    """Получить всех специалистов"""
    return get_users_by_role("Специалист")