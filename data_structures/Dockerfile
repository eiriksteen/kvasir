FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install --upgrade pip && \
    pip install -e .

CMD ["python", "-c", "import synesis_data_structures; print('Data structures package loaded successfully')"] 