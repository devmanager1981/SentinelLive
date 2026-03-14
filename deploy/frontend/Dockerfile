FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY web/ ./web/

EXPOSE 8501

ENV PYTHONUNBUFFERED=1

RUN mkdir -p /root/.streamlit && \
    printf '[server]\nheadless = true\nport = 8501\nenableCORS = false\nenableXsrfProtection = false\n' > /root/.streamlit/config.toml

CMD streamlit run web/app.py --server.port 8501 --server.address 0.0.0.0
