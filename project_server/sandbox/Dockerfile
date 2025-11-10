FROM python:3.13-slim

WORKDIR /app

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get install -y build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY schemas /app/schemas
COPY project_server/server /app/server

# Install synesis data structures package from source and the main package
RUN pip install --upgrade pip && \
    pip install -e /app/schemas && \
    pip install -e /app/server

CMD ["tail", "-f", "/dev/null"]
