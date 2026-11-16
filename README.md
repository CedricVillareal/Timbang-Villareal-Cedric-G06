# TIMBANG - Phase 1: Account feature (Django + PostgreSQL/Supabase)

```bash
python -m venv venv && venv\Scripts\activate     # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
copy .env.example .env                           # then fill in your database details
python manage.py makemigrations accounts         # required: custom user model
python manage.py migrate
python manage.py runserver
```

Create the PostgreSQL database first (`CREATE DATABASE timbang;`). For Supabase, use its
connection details in the `DB_*` variables and set `DB_SSLMODE=require`.

Roles: Owner and Staff. The first account registered becomes the Owner; later accounts are Staff.
