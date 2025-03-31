import streamlit as st
import requests
from dotenv import load_dotenv
import os
import extra_streamlit_components as stx
from datetime import datetime, timedelta


st.set_page_config(
    page_title="URL Shortener",
    layout="centered"
)

load_dotenv()


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_PREFIX = os.getenv("API_PREFIX")


@st.cache_resource(experimental_allow_widgets=True)
def get_cookie_manager():
    return stx.CookieManager(key="unique_cookie_manager")


cookie_manager = get_cookie_manager()


if 'is_authenticated' not in st.session_state:
    st.session_state.is_authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'access_token' not in st.session_state:
    st.session_state.access_token = None


token_from_cookie = cookie_manager.get("access_token")
username_from_cookie = cookie_manager.get("username")


if not st.session_state.is_authenticated and token_from_cookie and username_from_cookie:
    st.session_state.is_authenticated = True
    st.session_state.access_token = token_from_cookie
    st.session_state.username = username_from_cookie


def login(username: str, password: str) -> bool:
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/token",
            data={
                "username": username, 
                "password": password,
                "grant_type": "password"
            }
        )
        if response.status_code == 200:
            data = response.json()
            st.session_state.access_token = data["access_token"]
            st.session_state.is_authenticated = True
            st.session_state.username = username
            
            # 7 days cookie
            expiry = datetime.now() + timedelta(days=7)
            cookie_manager.set("access_token", data["access_token"], expires_at=expiry, key="set_token")
            cookie_manager.set("username", username, expires_at=expiry, key="set_username")
            
            st.success("Успешный логин")
            st.rerun()
            return True
        else:
            st.error("Не удалось войти")
        return False
    except Exception as e:
        st.error(f"Ошибка при входе: {str(e)}")
        return False


def register(username: str, password: str) -> bool:
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/register",
            json={"username": username, "password": password, "email": f"{username}@example.com"}
        )
        if response.status_code == 200:
            st.success("Успешная регистрация")
            return login(username, password)
        else:
            error_msg = "Ошибка при регистрации"
            try:
                error_data = response.json()
                if "detail" in error_data:
                    error_msg = f"Ошибка: {error_data['detail']}"
            except Exception:
                pass
            st.error(error_msg)
        return False
    except Exception as e:
        st.error(f"Ошибка при регистрации: {str(e)}")
        return False


def logout():
    st.session_state.is_authenticated = False
    st.session_state.username = None
    st.session_state.access_token = None

    cookie_manager.delete("access_token", key="delete_token")
    cookie_manager.delete("username", key="delete_username")

    st.rerun()


with st.sidebar:
    st.title("👤 Аккаунт")

    if not st.session_state.is_authenticated:
        tab1, tab2 = st.tabs(["Вход", "Регистрация"])
        
        with tab1:
            with st.form("login_form"):
                username = st.text_input("Имя юзера")
                password = st.text_input("Пароль", type="password")
                submit_login = st.form_submit_button("Войти")
                
                if submit_login:
                    if not username or not password:
                        st.error("Пожалуйста, заполните все поля")
                    else:
                        login(username, password)
        
        with tab2:
            with st.form("register_form"):
                new_username = st.text_input("Имя юзера")
                new_password = st.text_input("Пароль", type="password")
                confirm_password = st.text_input("Подтвердите пароль", type="password")
                submit_register = st.form_submit_button("Зарегистрироваться")
                
                if submit_register:
                    if not new_username or not new_password or not confirm_password:
                        st.error("Пожалуйста, заполните все поля")
                    elif new_password != confirm_password:
                        st.error("Пароли не совпадают")
                    else:
                        register(new_username, new_password)
    else:
        st.write(f"Здравствуйте, {st.session_state.username}!")
        if st.button("Выйти"):
            logout()


st.title("Сервис сокращения ссылок")
st.markdown("---")

with st.form("shorten_form"):
    original_url = st.text_input("Введите длинную ссылку")
    custom_alias = st.text_input("Пользовательский алиас (необязательно)")
    expires_at = st.date_input("Срок действия ссылки (необязательно)")
    
    submitted = st.form_submit_button("Сократить ссылку")
    
    if submitted:
        if not original_url:
            st.error("Пожалуйста, введите URL для сокращения")
        else:
            st.info("Функционал будет добавлен позже")

st.markdown("---")
st.subheader("📊 Поиск и статистика")
search_url = st.text_input("Поиск по оригинальной ссылке")
if st.button("Найти"):
    st.info("Функционал поиска будет добавлен позже")