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


def format_datetime(datetime_str: str) -> str:
    try:
        dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        return dt.strftime("%d.%m.%Y %H:%M")
    except Exception:
        return datetime_str


def display_link_details(link_data: dict, use_expander=True, show_controls=False):
    short_url = f"{API_BASE_URL}/{link_data['short_code']}"

    if use_expander:
        with st.expander("Детали ссылки"):
            _display_link_content(link_data, short_url, show_controls)
    else:
        _display_link_content(link_data, short_url, show_controls)


def _display_link_content(link_data: dict, short_url: str, show_controls=False):
    """Внутренняя функция для отображения содержимого ссылки"""
    st.write(f"**Короткая ссылка**: [{short_url}]({short_url})")
    st.write(f"**Оригинальный URL**: {link_data['original_url']}")
    st.write(f"**Короткий код**: {link_data['short_code']}")
    st.write(f"**Создана**: {format_datetime(link_data['created_at'])}")
    if link_data.get('expires_at'):
        st.write(f"**Истекает**: {format_datetime(link_data['expires_at'])}")
    st.write(f"**Количество переходов**: {link_data['clicks']}")

    if show_controls and st.session_state.is_authenticated:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Удалить", key=f"delete_{link_data['short_code']}"):
                try:
                    if delete_link(link_data['short_code']):
                        st.success(f"Ссылка {link_data['short_code']} успешно удалена")
                        st.rerun()
                except Exception as e:
                    st.error(f"Ошибка при удалении: {str(e)}")
        with col2:
            if st.button("Редактировать", key=f"edit_{link_data['short_code']}"):
                st.session_state[f"editing_{link_data['short_code']}"] = True

        if st.session_state.get(f"editing_{link_data['short_code']}", False):
            st.markdown("---")
            st.subheader("Редактирование ссылки")

            with st.form(key=f"edit_form_{link_data['short_code']}"):
                new_original_url = st.text_input(
                    "Новый оригинальный URL",
                    value=link_data['original_url'],
                    placeholder="https://example.com",
                    key=f"edit_url_{link_data['short_code']}"
                )
                st.caption("URL должен быть валидным. Если протокол не указан, будет добавлен https://")

                new_custom_alias = st.text_input(
                    "Новый короткий код (оставьте пустым, чтобы оставить текущий)",
                    value="",
                    placeholder=f"Текущий: {link_data['short_code']}",
                    key=f"edit_alias_{link_data['short_code']}"
                )

                include_expiry = st.checkbox(
                    "Установить срок действия",
                    key=f"edit_include_expiry_{link_data['short_code']}"
                )

                expiry_days = None
                if include_expiry:
                    expiry_days = st.number_input(
                        "Срок действия (дни)", 
                        min_value=1, 
                        max_value=365, 
                        value=30,
                        key=f"edit_expiry_{link_data['short_code']}"
                    )
                
                col1, col2 = st.columns(2)
                with col1:
                    submit = st.form_submit_button("Сохранить")
                with col2:
                    cancel = st.form_submit_button("Отмена")
                
                if cancel:
                    st.session_state.pop(f"editing_{link_data['short_code']}", None)
                    st.rerun()
                
                if submit:
                    try:
                        # Подготовка данных для обновления
                        expires_at = None
                        if include_expiry and expiry_days:
                            expires_at = (datetime.now() + timedelta(days=expiry_days)).isoformat()
                            
                        update_link(
                            link_data['short_code'],
                            original_url=new_original_url,
                            custom_alias=new_custom_alias if new_custom_alias else None,
                            expires_at=expires_at
                        )
                        
                        st.success("Ссылка успешно обновлена!")
                        st.session_state.pop(f"editing_{link_data['short_code']}", None)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Ошибка при обновлении: {str(e)}")


def get_user_links() -> list:
    try:
        if not st.session_state.is_authenticated:
            raise Exception("Пользователь не авторизован")

        headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
        response = requests.get(
            f"{API_BASE_URL}/links/user",
            headers=headers
        )

        if response.status_code == 200:
            return response.json()
        else:
            error_msg = "Ошибка при получении списка ссылок"
            try:
                error_data = response.json()
                if "detail" in error_data:
                    error_msg = f"Ошибка: {error_data['detail']}"
            except Exception:
                pass
            raise Exception(error_msg)
    except Exception as e:
        raise e


def delete_link(short_code: str) -> bool:
    """Удаление ссылки по короткому коду"""
    try:
        if not st.session_state.is_authenticated:
            raise Exception("Пользователь не авторизован")

        headers = {"Authorization": f"Bearer {st.session_state.access_token}"}

        response = requests.delete(
            f"{API_BASE_URL}/links/{short_code}",
            headers=headers
        )

        if response.status_code in [200, 204]:
            return True
        else:
            error_msg = "Ошибка при удалении ссылки"
            try:
                error_data = response.json()
                if "detail" in error_data:
                    error_msg = f"Ошибка: {error_data['detail']}"
            except Exception:
                pass
            raise Exception(error_msg)
    except Exception as e:
        raise e


def update_link(short_code: str, original_url: str = None, custom_alias: str = None, expires_at=None) -> dict:
    """Обновление ссылки по короткому коду"""
    try:
        if not st.session_state.is_authenticated:
            raise Exception("Пользователь не авторизован")
            
        headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
        
        data = {}
        if original_url:
            data["original_url"] = ensure_url_protocol(original_url)
        if custom_alias:
            data["custom_alias"] = custom_alias
        if expires_at:
            data["expires_at"] = expires_at
            
        response = requests.put(
            f"{API_BASE_URL}/links/{short_code}",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            error_msg = "Ошибка при обновлении ссылки"
            try:
                error_data = response.json()
                if "detail" in error_data:
                    error_msg = f"Ошибка: {error_data['detail']}"
            except Exception:
                pass
            raise Exception(error_msg)
    except Exception as e:
        raise e


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
        st.write(f"Здравствуйте, {st.session_state.username}.")
        if st.button("Выйти"):
            logout()


st.title("Сервис сокращения ссылок")

if not st.session_state.is_authenticated:
    st.info("""
    ⚠️ Вы не авторизованы.

    Созданные ссылки будут действительны только 1 день.

    Зарегистрируйтесь, чтобы получить дополнительные возможности:
    - Создавать ссылки с неограниченным сроком действия
    - Управлять своими ссылками (редактировать, удалять)
    """)

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
            expires_at = st.date_input(
                "Срок действия ссылки (необязательно)",
                min_value=datetime.now().date(),
                value=datetime.now().date() + timedelta(days=10),
                help="После этой даты ссылка станет недействительной"
            )

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
        st.header("Мои ссылки")

        try:
            user_links = get_user_links()

            if not user_links:
                st.info("У вас пока нет созданных ссылок. Создайте первую на вкладке 'Создать ссылку'")
            else:
                st.success(f"Найдено ссылок: {len(user_links)}")

                for idx, link in enumerate(user_links, 1):
                    with st.expander(f"{idx} - {link['original_url']}"):
                        display_link_details(link, use_expander=False, show_controls=True)

        except Exception as e:
            st.error(f"Ошибка при загрузке ссылок: {str(e)}")

    with tabs[2]:
        st.header("Поиск ссылок")

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
