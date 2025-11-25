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

# Copy kvasir-research directory for installation
COPY kvasir-research /app/kvasir-research

# Copy kvasir-ontology directory for installation
COPY kvasir-ontology /app/kvasir-ontology

# Install kvasir-ontology in editable mode
WORKDIR /app/kvasir-ontology
RUN pip install --no-cache-dir -e .

# Install kvasir-research in editable mode
WORKDIR /app/kvasir-research
RUN pip install --no-cache-dir -e .

