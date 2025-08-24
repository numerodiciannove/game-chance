

---

# Game Chance API — Setup and Testing

## Testing on VPS

The project is already running on a VPS. You can test the API functionality using Swagger/OpenAPI:

* Swagger UI: [http://185.230.88.82:5044/docs/](http://185.230.88.82:5044/docs/)
* ReDoc: [http://185.230.88.82:5044/redoc/](http://185.230.88.82:5044/redoc/)

---

## Local Testing with Docker

1. Clone the project:

```bash
git clone https://github.com/numerodiciannove/game-chance
cd game-chance
```

2. Create a `.env` file by copying `.env.sample` and set your secret key:

```bash
cp .env.sample .env
# Edit .env and set
# DJANGO_SECRET_KEY=YOUR_SECRET_KEY
```

3. Start the project with Docker:

```bash
docker-compose up --build
```

> After starting, the API will be available at `http://localhost:5044`.

---

## Local Setup without Docker

1. Clone the project:

```bash
git clone https://github.com/numerodiciannove/game-chance
cd game-chance
```

2. Create a virtual environment and activate it:

```bash
python -m venv venv
# Linux / macOS
source venv/bin/activate
# Windows
venv\Scripts\activate
```

3. Create a `.env` file by copying `.env.sample` and set your secret key:

```bash
cp .env.sample .env
# Edit .env and set
# DJANGO_SECRET_KEY=YOUR_SECRET_KEY
```

4. Install dependencies:

```bash
pip install -r requirements.txt
```

5. Apply migrations:

```bash
python manage.py migrate
```

6. Start the server:

```bash
python manage.py runserver 0.0.0.0:8000
```

> After starting, the API will be available at `http://localhost:8000`.
