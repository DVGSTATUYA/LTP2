import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import qrcode
from io import BytesIO
from datetime import datetime, timedelta
import time
import json

# Настройки
API_BASE_URL = "http://localhost:8000"
QR_CODE_URL = "https://docs.google.com/forms/d/e/1FAIpQLSepjRWo5ZL2OC0fn6hyMQIQZGCPr0C8CznVOhlOtcE7BlLTYQ/viewform?usp=dialog"

# Инициализация состояния сессии
def init_session_state():
    if 'access_token' not in st.session_state:
        st.session_state.access_token = None
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None
    if 'page' not in st.session_state:
        st.session_state.page = "main"
    if 'current_request_id' not in st.session_state:
        st.session_state.current_request_id = None

# API функции
def api_login(login: str, password: str):
    """Авторизация в API"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/token",
            data={"username": login, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except:
        return None

def api_register(user_data):
    """Регистрация пользователя"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/register",
            json=user_data
        )
        return response
    except:
        return None

def api_get(endpoint, params=None):
    """GET запрос к API"""
    if st.session_state.access_token:
        headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
        try:
            response = requests.get(
                f"{API_BASE_URL}{endpoint}",
                headers=headers,
                params=params
            )
            return response
        except:
            return None
    return None

def api_post(endpoint, data):
    """POST запрос к API"""
    if st.session_state.access_token:
        headers = {
            "Authorization": f"Bearer {st.session_state.access_token}",
            "Content-Type": "application/json"
        }
        try:
            response = requests.post(
                f"{API_BASE_URL}{endpoint}",
                headers=headers,
                json=data
            )
            return response
        except:
            return None
    return None

def api_put(endpoint, data):
    """PUT запрос к API"""
    if st.session_state.access_token:
        headers = {
            "Authorization": f"Bearer {st.session_state.access_token}",
            "Content-Type": "application/json"
        }
        try:
            response = requests.put(
                f"{API_BASE_URL}{endpoint}",
                headers=headers,
                json=data
            )
            return response
        except:
            return None
    return None

def api_delete(endpoint):
    """DELETE запрос к API"""
    if st.session_state.access_token:
        headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
        try:
            response = requests.delete(
                f"{API_BASE_URL}{endpoint}",
                headers=headers
            )
            return response
        except:
            return None
    return None

# Вспомогательные функции
def generate_qr_code(url):
    """Генерация QR кода"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img_bytes = BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    return img_bytes

def get_status_color(status):
    """Цвет статуса заявки"""
    colors = {
        "Новая заявка": "🔵",
        "В процессе ремонта": "🟡",
        "Ожидание комплектующих": "🟠",
        "Готова к выдаче": "🟢",
        "Завершена": "✅"
    }
    return colors.get(status, "⚪")

# Страницы приложения
def login_page():
    """Страница авторизации"""
    st.title("🔐 Авторизация")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            login = st.text_input("Логин", key="login_input")
            password = st.text_input("Пароль", type="password", key="password_input")
            submit = st.form_submit_button("Войти")
            
            if submit:
                if login and password:
                    with st.spinner("Авторизация..."):
                        token_data = api_login(login, password)
                        if token_data:
                            st.session_state.access_token = token_data["access_token"]
                            
                            # Получаем информацию о пользователе
                            response = api_get("/me")
                            if response and response.status_code == 200:
                                st.session_state.user_info = response.json()
                                st.success("Успешная авторизация!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Ошибка получения данных пользователя")
                        else:
                            st.error("Неверный логин или пароль")
                else:
                    st.warning("Заполните все поля")
        
        # Кнопка перехода к регистрации
        if st.button("Зарегистрироваться"):
            st.session_state.page = "register"
            st.rerun()

def register_page():
    """Страница регистрации"""
    st.title("📝 Регистрация")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("register_form"):
            fio = st.text_input("ФИО")
            phone = st.text_input("Номер телефона")
            login = st.text_input("Логин")
            password = st.text_input("Пароль", type="password")
            role = st.selectbox(
                "Роль",
                ["Заказчик", "Специалист", "Оператор", "Менеджер"],
                help="Менеджер может быть создан только другим менеджером"
            )
            
            submit = st.form_submit_button("Зарегистрироваться")
            
            if submit:
                if all([fio, phone, login, password]):
                    user_data = {
                        "fio": fio,
                        "phone": phone,
                        "login": login,
                        "password": password,
                        "role": role
                    }
                    
                    response = api_register(user_data)
                    if response:
                        if response.status_code == 200:
                            st.success("Регистрация успешна! Теперь вы можете войти.")
                            time.sleep(2)
                            st.session_state.page = "login"
                            st.rerun()
                        else:
                            try:
                                error_data = response.json()
                                st.error(f"Ошибка: {error_data.get('detail', 'Неизвестная ошибка')}")
                            except:
                                st.error("Ошибка при регистрации")
                    else:
                        st.error("Не удалось подключиться к серверу")
                else:
                    st.warning("Заполните все поля")
        
        if st.button("← Назад к авторизации"):
            st.session_state.page = "login"
            st.rerun()

def main_page():
    """Главная страница с QR-кодом"""
    st.title(f"👋 Добро пожаловать, {st.session_state.user_info['fio']}!")
    
    # Информация о пользователе
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**Роль:** {st.session_state.user_info['role']}")
    with col2:
        st.info(f"**Телефон:** {st.session_state.user_info['phone']}")
    
    st.markdown("---")
    
    # QR код для оценки работы
    st.header("📱 Оцените нашу работу!")
    st.markdown("""
    Мы стремимся к постоянному улучшению качества нашего сервиса. 
    Пожалуйста, оцените нашу работу, отсканировав QR-код ниже:
    """)
    
    # Генерация QR кода
    qr_img = generate_qr_code(QR_CODE_URL)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(qr_img, caption="QR-код для оценки сервиса", width="stretch")
    
    st.markdown(f"""
    Или перейдите по ссылке: [{QR_CODE_URL}]({QR_CODE_URL})
    
    Ваше мнение важно для нас и поможет нам стать лучше!
    """)
    
    st.markdown("---")
    
    # Общая статистика
    st.header("📊 Общая информация")
    
    if st.session_state.user_info["role"] in ["Менеджер", "Оператор"]:
        response = api_get("/requests")
        if response and response.status_code == 200:
            requests_data = response.json()
            
            col1, col2, col3 = st.columns(3)
            
            # Статистика по статусам
            status_counts = {}
            for req in requests_data:
                status = req.get("request_status", "Не указан")
                status_counts[status] = status_counts.get(status, 0) + 1
            
            with col1:
                st.metric("Всего заявок", len(requests_data))
            
            with col2:
                completed = sum(1 for req in requests_data 
                              if req.get("request_status") in ["Готова к выдаче", "Завершена"])
                st.metric("Выполнено", completed)
            
            with col3:
                in_progress = sum(1 for req in requests_data 
                                 if req.get("request_status") == "В процессе ремонта")
                st.metric("В работе", in_progress)
            
            # График распределения заявок
            if status_counts:
                fig = go.Figure(data=[go.Pie(
                    labels=list(status_counts.keys()),
                    values=list(status_counts.values()),
                    hole=.3,
                    marker_colors=px.colors.qualitative.Set3
                )])
                fig.update_layout(title="Распределение заявок по статусам")
                st.plotly_chart(fig, use_container_width=True)
    
    # Кнопка перехода к заявкам
    if st.button("📋 Перейти к заявкам", use_container_width=True):
        st.session_state.page = "requests"
        st.rerun()

def requests_page():
    """Страница работы с заявками"""
    st.title("📋 Заявки на ремонт")
    
    # Вкладки
    if st.session_state.user_info["role"] in ["Менеджер", "Оператор", "Специалист"]:
        tab1, tab2, tab3, tab4 = st.tabs(["📋 Текущие заявки", "➕ Создать", "✏️ Изменить", "🗑️ Удалить"])
    else:  # Заказчик
        tab1, tab2 = st.tabs(["📋 Мои заявки", "➕ Создать"])
    
    # Вкладка с текущими заявками
    with tab1:
        st.header("Текущие заявки")
        
        response = api_get("/requests")
        if response and response.status_code == 200:
            requests_data = response.json()
            
            if requests_data:
                # Фильтрация по роли
                if st.session_state.user_info["role"] == "Заказчик":
                    requests_data = [req for req in requests_data 
                                    if req.get("client_id") == st.session_state.user_info["user_id"]]
                elif st.session_state.user_info["role"] == "Специалист":
                    requests_data = [req for req in requests_data 
                                    if req.get("master_id") == st.session_state.user_info["user_id"]]
                
                if requests_data:
                    # Создаем DataFrame
                    df_data = []
                    for req in requests_data:
                        df_data.append({
                            "ID": req["request_id"],
                            "Дата": req["start_date"],
                            "Оборудование": req["climate_tech_type"],
                            "Модель": req["climate_tech_model"],
                            "Проблема": req["problem_description"],
                            "Статус": f"{get_status_color(req['request_status'])} {req['request_status']}",
                            "Мастер": f"ID: {req.get('master_id', 'Не назначен')}",
                            "Клиент": f"ID: {req.get('client_id')}"
                        })
                    
                    df = pd.DataFrame(df_data)
                    
                    # Поиск и фильтры
                    col1, col2 = st.columns(2)
                    with col1:
                        search = st.text_input("🔍 Поиск по оборудованию или проблеме")
                    with col2:
                        status_filter = st.multiselect(
                            "Фильтр по статусу",
                            options=["Новая заявка", "В процессе ремонта", "Ожидание комплектующих", 
                                    "Готова к выдаче", "Завершена"],
                            default=[]
                        )
                    
                    if search:
                        df = df[df.apply(lambda row: search.lower() in str(row["Оборудование"]).lower() or 
                                                    search.lower() in str(row["Проблема"]).lower(), axis=1)]
                    
                    if status_filter:
                        status_symbols = [get_status_color(s) for s in status_filter]
                        df = df[df["Статус"].str.contains('|'.join(status_symbols))]
                    
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    
                    # Детальный просмотр заявки
                    st.subheader("🔍 Детали заявки")
                    selected_id = st.selectbox(
                        "Выберите ID заявки для подробного просмотра",
                        options=df["ID"].tolist(),
                        key="request_detail_select"
                    )
                    
                    if selected_id:
                        detail_response = api_get(f"/requests/{selected_id}")
                        if detail_response and detail_response.status_code == 200:
                            request_detail = detail_response.json()
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Дата создания:** {request_detail['start_date']}")
                                st.write(f"**Тип оборудования:** {request_detail['climate_tech_type']}")
                                st.write(f"**Модель:** {request_detail['climate_tech_model']}")
                                if request_detail.get('completion_date'):
                                    st.write(f"**Дата завершения:** {request_detail['completion_date']}")
                            
                            with col2:
                                st.write(f"**Статус:** {request_detail['request_status']}")
                                st.write(f"**Клиент ID:** {request_detail['client_id']}")
                                if request_detail.get('master_id'):
                                    st.write(f"**Мастер ID:** {request_detail['master_id']}")
                                if request_detail.get('repair_parts'):
                                    st.write(f"**Запчасти:** {request_detail['repair_parts']}")
                            
                            st.write(f"**Описание проблемы:**")
                            st.info(request_detail['problem_description'])
                            
                            # Комментарии
                            comments_response = api_get(f"/requests/{selected_id}/comments")
                            if comments_response and comments_response.status_code == 200:
                                comments = comments_response.json()
                                if comments:
                                    st.subheader("💬 Комментарии")
                                    for comment in comments:
                                        with st.expander(f"Комментарий от {comment.get('master_name', 'ID:' + str(comment['master_id']))} "
                                                        f"({comment['created_at']})"):
                                            st.write(comment['message'])
                else:
                    st.info("Заявок не найдено")
            else:
                st.info("Заявок не найдено")
        else:
            st.error("Ошибка при загрузке заявок")
    
    # Вкладка создания заявки
    with tab2:
        st.header("Создать новую заявку")
        
        if st.session_state.user_info["role"] in ["Заказчик", "Оператор", "Менеджер"]:
            with st.form("create_request_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    start_date = st.date_input("Дата заявки", datetime.now())
                    climate_tech_type = st.text_input("Тип оборудования*", 
                                                     placeholder="Например: Кондиционер, Увлажнитель")
                    climate_tech_model = st.text_input("Модель оборудования*")
                
                with col2:
                    request_status = st.selectbox(
                        "Статус*",
                        ["Новая заявка", "В процессе ремонта", "Ожидание комплектующих"]
                    )
                    
                    # Получение списка специалистов для назначения
                    if st.session_state.user_info["role"] in ["Менеджер", "Оператор"]:
                        specialists_response = api_get("/users/specialists")
                        specialists = {}
                        if specialists_response and specialists_response.status_code == 200:
                            for spec in specialists_response.json():
                                specialists[spec["user_id"]] = f"{spec['fio']} (ID: {spec['user_id']})"
                        
                        master_id = st.selectbox(
                            "Назначить специалиста",
                            options=["Не назначен"] + list(specialists.values())
                        )
                        
                        # Преобразуем выбранного специалиста обратно в ID
                        master_id_value = None
                        if master_id != "Не назначен":
                            for uid, name in specialists.items():
                                if name == master_id:
                                    master_id_value = uid
                                    break
                    else:
                        master_id_value = None
                
                problem_description = st.text_area("Описание проблемы*", height=100)
                
                # Если пользователь - заказчик, автоматически подставляем его ID
                if st.session_state.user_info["role"] == "Заказчик":
                    client_id = st.session_state.user_info["user_id"]
                    st.info(f"Заявка будет создана от вашего имени (ID клиента: {client_id})")
                else:
                    client_id = st.number_input("ID клиента*", min_value=1, step=1)
                
                submit = st.form_submit_button("Создать заявку", use_container_width=True)
                
                if submit:
                    if all([climate_tech_type, climate_tech_model, problem_description]) and client_id:
                        request_data = {
                            "start_date": str(start_date),
                            "climate_tech_type": climate_tech_type,
                            "climate_tech_model": climate_tech_model,
                            "problem_description": problem_description,
                            "request_status": request_status,
                            "master_id": master_id_value,
                            "client_id": client_id
                        }
                        
                        response = api_post("/requests", request_data)
                        if response:
                            if response.status_code == 200:
                                st.success("Заявка успешно создана!")
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error(f"Ошибка: {response.json().get('detail', 'Неизвестная ошибка')}")
                        else:
                            st.error("Не удалось подключиться к серверу")
                    else:
                        st.warning("Пожалуйста, заполните все обязательные поля (помечены *)")
    
    # Вкладка изменения заявки
    if st.session_state.user_info["role"] in ["Менеджер", "Оператор", "Специалист"]:
        with tab3:
            st.header("Изменить заявку")
            
            # Получаем список заявок для выбора
            response = api_get("/requests")
            if response and response.status_code == 200:
                requests_list = response.json()
                
                # Фильтрация по роли
                if st.session_state.user_info["role"] == "Специалист":
                    requests_list = [req for req in requests_list 
                                    if req.get("master_id") == st.session_state.user_info["user_id"]]
                
                if requests_list:
                    request_options = {}
                    for req in requests_list:
                        request_options[req["request_id"]] = \
                            f"ID: {req['request_id']} - {req['climate_tech_type']} ({req['request_status']})"
                    
                    selected_request_id = st.selectbox(
                        "Выберите заявку для изменения",
                        options=list(request_options.keys()),
                        format_func=lambda x: request_options[x]
                    )
                    
                    if selected_request_id:
                        # Получаем детали заявки
                        detail_response = api_get(f"/requests/{selected_request_id}")
                        if detail_response and detail_response.status_code == 200:
                            request_detail = detail_response.json()
                            
                            with st.form("edit_request_form"):
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    new_status = st.selectbox(
                                        "Новый статус",
                                        ["Новая заявка", "В процессе ремонта", "Ожидание комплектующих", 
                                         "Готова к выдаче", "Завершена"],
                                        index=["Новая заявка", "В процессе ремонта", "Ожидание комплектующих", 
                                               "Готова к выдаче", "Завершена"].index(request_detail["request_status"])
                                    )
                                    
                                    # Для менеджера и оператора - возможность изменить специалиста
                                    if st.session_state.user_info["role"] in ["Менеджер", "Оператор"]:
                                        specialists_response = api_get("/users/specialists")
                                        specialists = {"Не назначен": None}
                                        if specialists_response and specialists_response.status_code == 200:
                                            for spec in specialists_response.json():
                                                specialists[f"{spec['fio']} (ID: {spec['user_id']})"] = spec["user_id"]
                                        
                                        current_master = next((k for k, v in specialists.items() 
                                                             if v == request_detail.get('master_id')), "Не назначен")
                                        selected_master = st.selectbox(
                                            "Специалист",
                                            options=list(specialists.keys()),
                                            index=list(specialists.keys()).index(current_master)
                                        )
                                        new_master_id = specialists[selected_master]
                                    else:
                                        new_master_id = request_detail.get('master_id')
                                
                                with col2:
                                    if new_status in ["Готова к выдаче", "Завершена"]:
                                        completion_date = st.date_input("Дата завершения", datetime.now())
                                    else:
                                        completion_date = None
                                    
                                    repair_parts = st.text_input("Запчасти", 
                                                                 value=request_detail.get('repair_parts', ''))
                                
                                new_problem_description = st.text_area(
                                    "Описание проблемы",
                                    value=request_detail["problem_description"],
                                    height=100
                                )
                                
                                submit = st.form_submit_button("Обновить заявку", use_container_width=True)
                                
                                if submit:
                                    update_data = {
                                        "request_status": new_status,
                                        "problem_description": new_problem_description,
                                        "master_id": new_master_id
                                    }
                                    
                                    if completion_date:
                                        update_data["completion_date"] = str(completion_date)
                                    if repair_parts:
                                        update_data["repair_parts"] = repair_parts
                                    
                                    response = api_put(f"/requests/{selected_request_id}", update_data)
                                    if response:
                                        if response.status_code == 200:
                                            st.success("Заявка успешно обновлена!")
                                            time.sleep(2)
                                            st.rerun()
                                        else:
                                            st.error(f"Ошибка: {response.json().get('detail', 'Неизвестная ошибка')}")
                                    else:
                                        st.error("Не удалось подключиться к серверу")
                else:
                    st.info("Нет доступных заявок для изменения")
    
    # Вкладка удаления заявки
    if st.session_state.user_info["role"] == "Менеджер":
        with tab4:
            st.header("Удалить заявку")
            st.warning("⚠️ Это действие нельзя отменить!")
            
            response = api_get("/requests")
            if response and response.status_code == 200:
                requests_list = response.json()
                
                if requests_list:
                    request_options = {}
                    for req in requests_list:
                        request_options[req["request_id"]] = \
                            f"ID: {req['request_id']} - {req['climate_tech_type']} ({req['request_status']})"
                    
                    selected_request_id = st.selectbox(
                        "Выберите заявку для удаления",
                        options=list(request_options.keys()),
                        format_func=lambda x: request_options[x],
                        key="delete_select"
                    )
                    
                    if selected_request_id:
                        st.error(f"Вы выбрали заявку ID: {selected_request_id}")
                        
                        # Подтверждение удаления
                        confirm = st.checkbox("Я подтверждаю удаление заявки")
                        
                        if confirm:
                            if st.button("🗑️ Удалить заявку", type="primary", use_container_width=True):
                                response = api_delete(f"/requests/{selected_request_id}")
                                if response:
                                    if response.status_code == 200:
                                        st.success("Заявка успешно удалена!")
                                        time.sleep(2)
                                        st.rerun()
                                    else:
                                        st.error(f"Ошибка: {response.json().get('detail', 'Неизвестная ошибка')}")
                                else:
                                    st.error("Не удалось подключиться к серверу")
                else:
                    st.info("Нет доступных заявок")
    
    # Кнопка возврата
    if st.button("← На главную"):
        st.session_state.page = "main"
        st.rerun()

def users_page():
    """Страница управления пользователями (только для менеджера)"""
    if st.session_state.user_info["role"] != "Менеджер":
        st.error("Доступ запрещен. Эта страница доступна только менеджерам.")
        if st.button("← Назад"):
            st.session_state.page = "main"
            st.rerun()
        return
    
    st.title("👥 Управление пользователями")
    
    # Получение списка пользователей
    response = api_get("/users")
    if response and response.status_code == 200:
        users_data = response.json()
        
        if users_data:
            # Создаем DataFrame
            df_data = []
            for user in users_data:
                df_data.append({
                    "ID": user["user_id"],
                    "ФИО": user["fio"],
                    "Телефон": user["phone"],
                    "Логин": user["login"],
                    "Роль": user["role"]
                })
            
            df = pd.DataFrame(df_data)
            
            # Поиск
            search = st.text_input("🔍 Поиск по ФИО или логину")
            if search:
                df = df[df.apply(lambda row: search.lower() in str(row["ФИО"]).lower() or 
                                            search.lower() in str(row["Логин"]).lower(), axis=1)]
            
            # Фильтр по роли
            role_filter = st.multiselect(
                "Фильтр по роли",
                options=["Менеджер", "Оператор", "Специалист", "Заказчик"],
                default=[]
            )
            if role_filter:
                df = df[df["Роль"].isin(role_filter)]
            
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Статистика по ролям
            st.subheader("📊 Статистика по ролям")
            role_counts = df["Роль"].value_counts()
            
            cols = st.columns(len(role_counts))
            for idx, (role, count) in enumerate(role_counts.items()):
                with cols[idx]:
                    st.metric(role, count)
            
            # График распределения по ролям
            fig = px.pie(
                names=role_counts.index,
                values=role_counts.values,
                title="Распределение пользователей по ролям",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Пользователей не найдено")
    else:
        st.error("Ошибка при загрузке данных пользователей")
    
    if st.button("← На главную"):
        st.session_state.page = "main"
        st.rerun()

def comments_page():
    """Страница комментариев"""
    if st.session_state.user_info["role"] == "Заказчик":
        st.error("Доступ запрещен. Эта страница недоступна для заказчиков.")
        if st.button("← Назад"):
            st.session_state.page = "main"
            st.rerun()
        return
    
    st.title("💬 Комментарии")
    
    # Получаем все заявки пользователя
    response = api_get("/requests")
    if response and response.status_code == 200:
        requests_data = response.json()
        
        # Фильтрация по роли
        if st.session_state.user_info["role"] == "Специалист":
            requests_data = [req for req in requests_data 
                            if req.get("master_id") == st.session_state.user_info["user_id"]]
        
        if requests_data:
            # Выбор заявки
            request_options = {}
            for req in requests_data:
                request_options[req["request_id"]] = \
                    f"ID: {req['request_id']} - {req['climate_tech_type']} ({req['request_status']})"
            
            selected_request_id = st.selectbox(
                "Выберите заявку для просмотра комментариев",
                options=list(request_options.keys()),
                format_func=lambda x: request_options[x]
            )
            
            if selected_request_id:
                # Получаем комментарии
                comments_response = api_get(f"/requests/{selected_request_id}/comments")
                if comments_response and comments_response.status_code == 200:
                    comments = comments_response.json()
                    
                    if comments:
                        st.subheader(f"Комментарии к заявке ID: {selected_request_id}")
                        
                        for comment in comments:
                            with st.container():
                                col1, col2 = st.columns([3, 1])
                                with col1:
                                    st.markdown(f"**{comment.get('master_name', 'ID:' + str(comment['master_id']))}**")
                                    st.write(comment['message'])
                                with col2:
                                    st.caption(comment['created_at'])
                                st.divider()
                    else:
                        st.info("Нет комментариев для этой заявки")
                    
                    # Добавление нового комментария
                    st.subheader("Добавить комментарий")
                    with st.form("add_comment_form"):
                        new_comment = st.text_area("Текст комментария", height=100)
                        submit = st.form_submit_button("Добавить комментарий")
                        
                        if submit and new_comment:
                            comment_data = {
                                "message": new_comment,
                                "request_id": selected_request_id
                            }
                            
                            response = api_post(f"/requests/{selected_request_id}/comments", comment_data)
                            if response:
                                if response.status_code == 200:
                                    st.success("Комментарий добавлен!")
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error(f"Ошибка: {response.json().get('detail', 'Неизвестная ошибка')}")
                            else:
                                st.error("Не удалось подключиться к серверу")
        else:
            st.info("Нет доступных заявок")
    else:
        st.error("Ошибка при загрузке заявок")
    
    if st.button("← На главную"):
        st.session_state.page = "main"
        st.rerun()

def statistics_page():
    """Страница статистики"""
    st.title("📊 Статистика")
    
    user_role = st.session_state.user_info["role"]
    
    if user_role == "Менеджер":
        # Для менеджера - статистика по всем и выбор пользователя
        tab1, tab2 = st.tabs(["Общая статистика", "Статистика по пользователям"])
        
        with tab1:
            st.header("Общая статистика системы")
            
            # Получаем всю статистику
            response = api_get("/stats/all")
            if response and response.status_code == 200:
                stats = response.json()
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Выполнено заявок", stats["completed_requests_count"])
                
                with col2:
                    avg_time = stats["average_completion_time_days"]
                    if avg_time:
                        st.metric("Среднее время (дней)", f"{avg_time:.1f}")
                    else:
                        st.metric("Среднее время (дней)", "Нет данных")
                
                with col3:
                    # Получаем общее количество заявок
                    requests_response = api_get("/requests")
                    if requests_response and requests_response.status_code == 200:
                        total_requests = len(requests_response.json())
                        st.metric("Всего заявок", total_requests)
                
                # Статистика по проблемам
                if stats["problem_statistics"]:
                    st.subheader("Распределение по типам проблем")
                    
                    problems_df = pd.DataFrame(stats["problem_statistics"])
                    
                    # Исправляем имена колонок
                    # Проверяем, какие колонки есть в DataFrame
                    if 'problem_type' in problems_df.columns and 'count' in problems_df.columns:
                        # Если колонки называются 'problem_type' и 'count'
                        problems_df = problems_df.rename(columns={
                            "problem_type": "Тип проблемы", 
                            "count": "Количество"
                        })
                    elif 'problem_type' in problems_df.columns and 'cnt' in problems_df.columns:
                        # Если колонки называются 'problem_type' и 'cnt'
                        problems_df = problems_df.rename(columns={
                            "problem_type": "Тип проблемы", 
                            "cnt": "Количество"
                        })
                    else:
                        # Если имена колонок другие, просто используем их как есть
                        st.write("Доступные колонки:", problems_df.columns.tolist())
                        # Используем первую колонку как тип проблемы, вторую как количество
                        if len(problems_df.columns) >= 2:
                            problems_df = problems_df.rename(columns={
                                problems_df.columns[0]: "Тип проблемы",
                                problems_df.columns[1]: "Количество"
                            })
                    
                    # Отображаем DataFrame для отладки
                    st.write("Данные для графика:")
                    st.write(problems_df)
                    
                    # Проверяем, есть ли нужные колонки
                    if "Тип проблемы" in problems_df.columns and "Количество" in problems_df.columns:
                        # Ограничиваем длину текста для лучшего отображения
                        problems_df["Тип проблемы"] = problems_df["Тип проблемы"].apply(
                            lambda x: (x[:50] + "...") if len(x) > 50 else x
                        )
                        
                        fig = px.bar(
                            problems_df,
                            x="Тип проблемы",
                            y="Количество",
                            title="Количество заявок по типам проблем",
                            color="Количество",
                            color_continuous_scale="Blues"
                        )
                        fig.update_layout(xaxis_tickangle=-45)
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.error(f"Не найдены нужные колонки. Доступные колонки: {problems_df.columns.tolist()}")
            else:
                st.error("Ошибка при загрузке статистики")
        
        with tab2:
            st.header("Статистика по пользователям")
            
            # Получаем список пользователей
            users_response = api_get("/users")
            if users_response and users_response.status_code == 200:
                users = users_response.json()
                
                # Выбор пользователя
                user_options = {u["user_id"]: f"{u['fio']} ({u['role']})" for u in users}
                selected_user_id = st.selectbox(
                    "Выберите пользователя",
                    options=list(user_options.keys()),
                    format_func=lambda x: user_options[x]
                )
                
                if selected_user_id:
                    # Получаем заявки пользователя
                    requests_response = api_get("/requests")
                    if requests_response and requests_response.status_code == 200:
                        all_requests = requests_response.json()
                        
                        # Фильтруем заявки по роли пользователя
                        selected_user = next((u for u in users if u["user_id"] == selected_user_id), None)
                        if selected_user:
                            user_requests = []
                            if selected_user["role"] == "Заказчик":
                                user_requests = [r for r in all_requests if r.get("client_id") == selected_user_id]
                            elif selected_user["role"] == "Специалист":
                                user_requests = [r for r in all_requests if r.get("master_id") == selected_user_id]
                            elif selected_user["role"] == "Оператор":
                                # Операторы работают со всеми заявками
                                user_requests = all_requests
                            
                            if user_requests:
                                st.subheader(f"Статистика для {selected_user['fio']}")
                                
                                col1, col2, col3 = st.columns(3)
                                
                                with col1:
                                    total = len(user_requests)
                                    st.metric("Всего заявок", total)
                                
                                with col2:
                                    completed = sum(1 for r in user_requests 
                                                   if r.get("request_status") in ["Готова к выдаче", "Завершена"])
                                    st.metric("Выполнено", completed)
                                
                                with col3:
                                    if completed > 0 and total > 0:
                                        efficiency = (completed / total) * 100
                                        st.metric("Эффективность", f"{efficiency:.1f}%")
                                    else:
                                        st.metric("Эффективность", "0%")
                                
                                # График распределения по статусам
                                status_counts = {}
                                for req in user_requests:
                                    status = req.get("request_status", "Не указан")
                                    status_counts[status] = status_counts.get(status, 0) + 1
                                
                                if status_counts:
                                    fig = go.Figure(data=[go.Pie(
                                        labels=list(status_counts.keys()),
                                        values=list(status_counts.values()),
                                        hole=.3,
                                        title="Распределение заявок по статусам"
                                    )])
                                    st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.info("У пользователя нет заявок")
                                
    elif user_role == "Специалист":
        # Для специалиста - его личная статистика
        st.header("Ваша статистика")
        
        # Получаем заявки специалиста
        requests_response = api_get("/requests")
        if requests_response and requests_response.status_code == 200:
            all_requests = requests_response.json()
            specialist_requests = [r for r in all_requests 
                                  if r.get("master_id") == st.session_state.user_info["user_id"]]
            
            if specialist_requests:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    total = len(specialist_requests)
                    st.metric("Всего заявок", total)
                
                with col2:
                    completed = sum(1 for r in specialist_requests 
                                   if r.get("request_status") in ["Готова к выдаче", "Завершена"])
                    st.metric("Выполнено", completed)
                
                with col3:
                    if completed > 0 and total > 0:
                        efficiency = (completed / total) * 100
                        st.metric("Эффективность", f"{efficiency:.1f}%")
                    else:
                        st.metric("Эффективность", "0%")
                
                # Время выполнения заявок
                completion_times = []
                for req in specialist_requests:
                    if req.get("completion_date") and req.get("start_date"):
                        try:
                            start = datetime.strptime(req["start_date"], "%Y-%m-%d")
                            end = datetime.strptime(req["completion_date"], "%Y-%m-%d")
                            days = (end - start).days
                            if days >= 0:
                                completion_times.append(days)
                        except:
                            pass
                
                if completion_times:
                    avg_time = sum(completion_times) / len(completion_times)
                    st.metric("Среднее время выполнения (дней)", f"{avg_time:.1f}")
                    
                    # Гистограмма времени выполнения
                    fig = px.histogram(
                        x=completion_times,
                        nbins=10,
                        title="Распределение времени выполнения заявок",
                        labels={"x": "Дней на выполнение", "y": "Количество заявок"}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # График по типам оборудования
                equipment_counts = {}
                for req in specialist_requests:
                    equipment = req.get("climate_tech_type", "Не указано")
                    equipment_counts[equipment] = equipment_counts.get(equipment, 0) + 1
                
                if equipment_counts:
                    fig = px.bar(
                        x=list(equipment_counts.keys()),
                        y=list(equipment_counts.values()),
                        title="Распределение заявок по типам оборудования",
                        labels={"x": "Тип оборудования", "y": "Количество"}
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("У вас пока нет заявок")
        else:
            st.error("Ошибка при загрузке данных")
    else:
        st.info("Статистика доступна только менеджерам и специалистам")
    
    if st.button("← На главную"):
        st.session_state.page = "main"
        st.rerun()

def main():
    """Основная функция приложения"""
    # Настройки страницы
    st.set_page_config(
        page_title="Учет заявок на ремонт",
        page_icon="🔧",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Инициализация состояния
    init_session_state()
    
    # Проверка авторизации
    if not st.session_state.access_token:
        # Страница выбора: вход или регистрация
        if st.session_state.page == "register":
            register_page()
        else:
            login_page()
    else:
        # Отображаем боковую панель с навигацией
        with st.sidebar:
            st.title("🔧 Сервисный центр")
            st.markdown(f"**{st.session_state.user_info['fio']}**")
            st.caption(f"Роль: {st.session_state.user_info['role']}")
            st.divider()
            
            # Навигация
            if st.button("🏠 Главная", use_container_width=True):
                st.session_state.page = "main"
                st.rerun()
            
            if st.button("📋 Заявки", use_container_width=True):
                st.session_state.page = "requests"
                st.rerun()
            
            if st.session_state.user_info["role"] == "Менеджер":
                if st.button("👥 Пользователи", use_container_width=True):
                    st.session_state.page = "users"
                    st.rerun()
            
            if st.session_state.user_info["role"] != "Заказчик":
                if st.button("💬 Комментарии", use_container_width=True):
                    st.session_state.page = "comments"
                    st.rerun()
            
            if st.session_state.user_info["role"] in ["Менеджер", "Специалист"]:
                if st.button("📊 Статистика", use_container_width=True):
                    st.session_state.page = "statistics"
                    st.rerun()
            
            st.divider()
            
            # Выход
            if st.button("🚪 Выйти", use_container_width=True):
                st.session_state.access_token = None
                st.session_state.user_info = None
                st.session_state.page = "main"
                st.rerun()
        
        # Основной контент
        if st.session_state.page == "main":
            main_page()
        elif st.session_state.page == "requests":
            requests_page()
        elif st.session_state.page == "users":
            users_page()
        elif st.session_state.page == "comments":
            comments_page()
        elif st.session_state.page == "statistics":
            statistics_page()

if __name__ == "__main__":
    main()