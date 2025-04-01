import streamlit as st
import requests
from dotenv import load_dotenv
import os
import extra_streamlit_components as stx
from datetime import datetime, timedelta
import re


st.set_page_config(
    page_title="URL Shortener",
    layout="centered"
)

load_dotenv()


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

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


def ensure_url_protocol(url: str) -> str:
    if url and not re.match(r'^https?://', url):
        return f"https://{url}"
    return url


def create_short_link(original_url: str, custom_alias: str = None, expires_at=None) -> dict:
    try:
        original_url = ensure_url_protocol(original_url)
        headers = {}

        if st.session_state.is_authenticated:
            headers["Authorization"] = f"Bearer {st.session_state.access_token}"

        data = {"original_url": original_url}
        if custom_alias:
            data["custom_alias"] = custom_alias
        if expires_at:
            data["expires_at"] = expires_at.isoformat()

        response = requests.post(
            f"{API_BASE_URL}/links/shorten",
            json=data,
            headers=headers
        )

        if response.status_code == 200:
            return response.json()
        else:
            error_msg = "Ошибка при создании ссылки"
            try:
                error_data = response.json()
                if "detail" in error_data:
                    error_msg = f"Ошибка: {error_data['detail']}"
            except Exception:
                pass
            raise Exception(error_msg)
    except Exception as e:
        raise e


def search_links(original_url: str) -> list:
    try:
        headers = {}
        if st.session_state.is_authenticated:
            headers["Authorization"] = f"Bearer {st.session_state.access_token}"

        response = requests.get(
            f"{API_BASE_URL}/search",
            params={"original_url": original_url},
            headers=headers
        )

        if response.status_code == 200:
            return response.json()
        else:
            error_msg = "Ошибка при поиске ссылок"
            try:
                error_data = response.json()
                if "detail" in error_data:
                    error_msg = f"Ошибка: {error_data['detail']}"
            except Exception:
                pass
            raise Exception(error_msg)
    except Exception as e:
        raise e


def display_link_details(link_data: dict, use_expander=True):
    short_url = f"{API_BASE_URL}/{link_data['short_code']}"

    if use_expander:
        with st.expander("Детали ссылки"):
            _display_link_content(link_data, short_url)
    else:
        _display_link_content(link_data, short_url)


def _display_link_content(link_data: dict, short_url: str):
    st.write(f"**Короткая ссылка**: [{short_url}]({short_url})")
    st.write(f"**Оригинальный URL**: {link_data['original_url']}")
    st.write(f"**Короткий код**: {link_data['short_code']}")
    st.write(f"**Создана**: {link_data['created_at']}")
    if link_data.get('expires_at'):
        st.write(f"**Истекает**: {link_data['expires_at']}")
    st.write(f"**Количество переходов**: {link_data['clicks']}")

    # check is owner
    if st.session_state.is_authenticated and link_data.get('user_id') == st.session_state.get('user_id'):
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Удалить", key=f"delete_{link_data['short_code']}"):
                st.info("Функционал удаления будет добавлен позже")
        with col2:
            if st.button("Редактировать", key=f"edit_{link_data['short_code']}"):
                st.info("Функционал редактирования будет добавлен позже")


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


if not st.session_state.is_authenticated:    
    link_result = None

    with st.form("shorten_form_guest"):
        original_url = st.text_input("Введите длинную ссылку")
        submitted = st.form_submit_button("Сократить ссылку")

        if submitted:
            if not original_url:
                st.error("Введите URL для сокращения")
            else:
                try:
                    link_result = create_short_link(original_url)
                except Exception as e:
                    st.error(f"Не удалось создать короткую ссылку: {str(e)}")

    if link_result:
        short_url = f"{API_BASE_URL}/{link_result['short_code']}"
        st.success("Ссылка успешно создана!")
        col1, col2 = st.columns([3, 1])
        with col1:
            st.code(short_url)
        with col2:
            js_code = f"<script>navigator.clipboard.writeText('{short_url}');</script>"
            st.button("Копировать", on_click=lambda: st.write(js_code, unsafe_allow_html=True))

        display_link_details(link_result)

    st.markdown("---")
    st.subheader("Поиск ссылки")
    search_url = st.text_input("Поиск по оригинальной ссылке")
    if st.button("Найти"):
        if not search_url:
            st.error("Введите URL для поиска")
        else:
            try:
                results = search_links(search_url)
                if not results:
                    st.warning("Ссылки не найдены")
                else:
                    st.success(f"Найдено ссылок: {len(results)}")
                    for idx, link in enumerate(results, 1):
                        with st.expander(f"Результат {idx}: {link['short_code']}"):
                            display_link_details(link, use_expander=False)
            except Exception as e:
                st.error(f"Ошибка при поиске: {str(e)}")

else:
    tabs = st.tabs(["Создать ссылку", "Мои ссылки", "Поиск"])

    with tabs[0]:
        auth_link_result = None

        with st.form("shorten_form_auth"):
            original_url = st.text_input("Введите длинную ссылку")
            custom_alias = st.text_input("Пользовательский алиас (необязательно)")
            expires_at = st.date_input("Срок действия ссылки (необязательно)")

            submitted = st.form_submit_button("Сократить ссылку")

            if submitted:
                if not original_url:
                    st.error("Пожалуйста, введите URL для сокращения")
                else:
                    try:
                        if expires_at:
                            expiry_datetime = datetime.combine(expires_at, datetime.max.time())
                        else:
                            expiry_datetime = None

                        auth_link_result = create_short_link(original_url, custom_alias, expiry_datetime)
                    except Exception as e:
                        st.error(f"Не удалось создать короткую ссылку: {str(e)}")

        if auth_link_result:
            short_url = f"{API_BASE_URL}/{auth_link_result['short_code']}"
            st.success("Ссылка успешно создана!")

            col1, col2 = st.columns([3, 1])
            with col1:
                st.code(short_url)
            with col2:
                js_code = f"<script>navigator.clipboard.writeText('{short_url}');</script>"
                st.button("Копировать", on_click=lambda: st.write(js_code, unsafe_allow_html=True))

            display_link_details(auth_link_result)

    with tabs[1]:
        st.subheader("Мои ссылки")
        st.info("Здесь будет список ваших ссылок с возможностью управления (скоро)")

    with tabs[2]:
        st.subheader("Поиск ссылки")
        search_url = st.text_input("Поиск по оригинальной ссылке")
        if st.button("Найти"):
            if not search_url:
                st.error("Введите URL для поиска")
            else:
                try:
                    results = search_links(search_url)
                    if not results:
                        st.warning("Ссылки не найдены")
                    else:
                        st.success(f"Найдено ссылок: {len(results)}")
                        for idx, link in enumerate(results, 1):
                            with st.expander(f"Результат {idx}: {link['short_code']}"):
                                display_link_details(link, use_expander=False)
                except Exception as e:
                    st.error(f"Ошибка при поиске: {str(e)}")
