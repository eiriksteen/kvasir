FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install --upgrade pip && \
    pip install -e .

EXPOSE 8000

CMD ["uvicorn", "src.synesis_api.main:app", "--host", "0.0.0.0", "--port", "8000"] 