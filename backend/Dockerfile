# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    AWS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
    REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

WORKDIR /app

RUN apt-get update \
    && apt-get install --yes --no-install-recommends tesseract-ocr \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system beforecommit \
    && useradd --system --gid beforecommit --home-dir /app beforecommit

COPY backend/requirements.txt ./requirements.txt
RUN --mount=type=secret,id=corporate_ca,required=false \
    if [ -s /run/secrets/corporate_ca ]; then \
        cp /run/secrets/corporate_ca /usr/local/share/ca-certificates/corporate-ca.crt; \
        update-ca-certificates; \
    fi \
    && PIP_CERT=/etc/ssl/certs/ca-certificates.crt python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt

COPY backend/app ./app

RUN chown -R beforecommit:beforecommit /app
USER beforecommit

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]