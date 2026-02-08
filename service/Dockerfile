FROM python:3.11-slim

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

# for psycopg2
RUN apt update && \
    apt install --no-install-recommends --no-install-suggests --assume-yes \
    gcc \
    libpq-dev \
    python-dev-is-python3

RUN python -m pip install --upgrade pip

RUN mkdir -p /app/service
WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

ADD . /app/service


CMD ["python", "-m", "service"]