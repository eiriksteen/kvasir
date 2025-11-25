FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    && curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null \
    && apt-get update \
    && apt-get install -y docker-ce-cli \
    && rm -rf /var/lib/apt/lists/*

COPY agents /app/agents
COPY ontology /app/ontology

WORKDIR /app/agents
RUN pip install --no-cache-dir -e .

WORKDIR /app/ontology
RUN pip install --no-cache-dir -e .


