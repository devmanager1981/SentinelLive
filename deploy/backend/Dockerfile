FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server/ ./server/

EXPOSE 8080

ENV PORT=8080
ENV PYTHONUNBUFFERED=1

CMD uvicorn server.main:app --host 0.0.0.0 --port ${PORT}
