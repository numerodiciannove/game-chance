FROM python:3.10
LABEL mainteiner="rmuraviov.dev@gmail.com"

ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libmariadb-dev \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --upgrade pip

WORKDIR /191919
COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY . .
