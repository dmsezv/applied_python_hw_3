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

## Установка и запуск

1. Клонировать репозиторий

```bash
git clone [repository-url]
```

2. Создать виртуальное окружение и установить зависимости

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Создать базу данных PostgreSQL

```bash
createdb url_shortener
```

4. Запустить сервер

```bash
uvicorn app.main:app --reload
```

## API Endpoints

- `POST /links/shorten` - создание короткой ссылки
- `GET /{short_code}` - переход по короткой ссылке
- `GET /links/{short_code}` - информация о ссылке
- `PUT /links/{short_code}` - обновление ссылки
- `DELETE /links/{short_code}` - удаление ссылки
- `GET /links/{short_code}/stats` - статистика по ссылке
- `GET /links/search` - поиск по оригинальному URL
