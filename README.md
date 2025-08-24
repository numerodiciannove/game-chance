

---

# Game Chance API — Setup and Testing

## Testing on VPS

The project is already running on a VPS. You can test the API functionality using Swagger/OpenAPI:

* Swagger UI: [http://185.230.88.82:5044/docs/](http://185.230.88.82:5044/docs/)
* ReDoc: [http://185.230.88.82:5044/redoc/](http://185.230.88.82:5044/redoc/)

---

## Local Testing with Docker

```bash
git clone https://github.com/numerodiciannove/game-chance
cd game-chance
docker-compose up --build
```

> After starting, the API will be available at `http://localhost:5044`.

---

## Local Setup without Docker

```bash
git clone https://github.com/numerodiciannove/game-chance
cd game-chance
python -m venv venv
# Linux / macOS
source venv/bin/activate
# Windows
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

> After starting, the API will be available at `http://localhost:8000`.
