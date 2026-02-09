# KanMind Backend

Django REST Framework API for the KanMind board/task application. Token-based authentication; resource-oriented API for auth, boards, and tasks.

**Application code lives in the [`backend/`](backend/) directory.** All commands below must be run from inside `backend/`.

## Requirements

- Python 3.10+
- See [`backend/requirements.txt`](backend/requirements.txt) for dependencies.

## Quick Start

1. **Clone the repository.**

2. **Go into the backend directory and create a virtual environment:**

   ```bash
   cd backend
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Environment variables:**

   Copy `backend/.env.example` to `backend/.env` and set at least:

   - `SECRET_KEY` – Django secret (use a random string).
   - Optionally: `DEBUG`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS` (for production).

   The database file (`db.sqlite3`) is created inside `backend/` automatically; do not commit it to Git.

5. **Run migrations** (from `backend/`):

   ```bash
   python manage.py migrate
   ```

6. **Start the server** (from `backend/`):

   ```bash
   python manage.py runserver
   ```

   API base URL: `http://127.0.0.1:8000/api/`

## Special Features

- **Guest user:** To enable the frontend "Guest login" button, run once from `backend/`:
  ```bash
  cd backend
  python manage.py create_guest_user
  ```
  Credentials match `GUEST_LOGIN` in the frontend config (email/password).

- **CORS:** When `DEBUG=True`, all origins are allowed so the frontend (e.g. Live Server on another port) can call the API. For production, set `CORS_ALLOWED_ORIGINS` in `.env`.

- **Admin:** Django admin is available at `/admin/`. From `backend/`, run `python manage.py createsuperuser` to manage boards, tasks, and users.

## Project Structure

- **Repository root:** This README; `.gitignore`; application code in **`backend/`**.
- **Inside `backend/`:** Django project **`core`** (settings, main URLs), `manage.py`, `requirements.txt`, `.env.example`.
- **Apps:** `auth_app` (registration, login, email-check), `board_app` (boards CRUD), `tasks_app` (tasks and comments).
- Each app has an `api/` folder with `views.py`, `serializers.py`, `urls.py`, `permissions.py`.

## API Overview

- **Auth:** `POST /api/registration/`, `POST /api/login/`, `GET /api/email-check/?email=...`
- **Boards:** `GET/POST /api/boards/`, `GET/PATCH/DELETE /api/boards/{id}/`
- **Tasks:** `GET /api/tasks/assigned-to-me/`, `GET /api/tasks/reviewing/`, `POST /api/tasks/`, `PATCH/DELETE /api/tasks/{id}/`, `GET/POST /api/tasks/{id}/comments/`, `DELETE /api/tasks/{id}/comments/{comment_id}/`

Send the token in the header: `Authorization: Token <your-token>` for protected endpoints.

## Database

- Do not commit `db.sqlite3` or any database dumps to version control. The repo `.gitignore` excludes them.
