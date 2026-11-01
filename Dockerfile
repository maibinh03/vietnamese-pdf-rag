FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/models/huggingface

WORKDIR /app

COPY requirements.txt .
COPY constraints.txt .

RUN pip install --no-cache-dir \
    torch==2.6.0 \
    --index-url https://download.pytorch.org/whl/cpu

RUN pip install --no-cache-dir -c constraints.txt -r requirements.txt

COPY bank_rag ./bank_rag

RUN mkdir -p /app/data

EXPOSE 8000

CMD ["uvicorn", "bank_rag.main:app", "--host", "0.0.0.0", "--port", "8000"]
