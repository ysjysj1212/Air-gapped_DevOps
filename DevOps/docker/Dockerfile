FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential docker-cli \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN python -m pip install --upgrade pip \
    && pip install -r requirements.txt

COPY run.py .
COPY sandbox.sh .
COPY src ./src
COPY templates ./templates
COPY ci-samples ./ci-samples
COPY docs ./docs

RUN chmod +x /app/sandbox.sh

EXPOSE 5000

CMD ["python", "run.py"]
