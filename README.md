# URL Shortener Service

Сервис для сокращения URL-ссылок с возможностью аналитики и управления.

## Функциональность

- Создание коротких ссылок
- Кастомные алиасы для ссылок
- Статистика переходов
- Управление сроком жизни ссылок
- Поиск по оригинальному URL
- Авторизация пользователей

## Технологии

- FastAPI
- PostgreSQL
- SQLAlchemy
- JWT для авторизации
- Streamlit (фронтенд)
- Docker и Docker Compose для развертывания

## Демонстрация проекта

Я добавил фронт на Streamlit для удобной и красивой демонстрации функционала.

### Функционал незарегистрированного пользователя

![Функционал без авторизации](screens/unauth_funcs.gif)

### Регистрация и авторизация

![Регистрация](screens/registration.gif)

### Создание ссылок

![Создание ссылок](screens/create_link.gif)

### Обновление ссылок

![Обновление ссылок](screens/update_link.gif)

### Удаление ссылок

![Удаление ссылок](screens/delete_link.gif)

## Доступ к приложениям:

- Frontend (Streamlit): http://localhost:8501
- Backend API: http://localhost:8000
- API документация: http://localhost:8000/docs

## API Endpoints

- `POST /links/shorten` - создание короткой ссылки
- `GET /{short_code}` - переход по короткой ссылке
- `GET /links/{short_code}` - информация о ссылке
- `PUT /links/{short_code}` - обновление ссылки
- `DELETE /links/{short_code}` - удаление ссылки
- `GET /links/{short_code}/stats` - статистика по ссылке
- `GET /links/search` - поиск по оригинальному URL
