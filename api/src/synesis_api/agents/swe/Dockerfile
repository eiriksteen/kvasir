FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    git \
    apt-utils \
    make \
    build-essential \
    libssl-dev \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    wget \
    curl \
    llvm \
    libncursesw5-dev \
    xz-utils \
    tk-dev \
    libxml2-dev \
    libxmlsec1-dev \
    libffi-dev \
    liblzma-dev \
    && rm -rf /var/lib/apt/lists/*

ENV PYENV_ROOT /root/.pyenv
ENV PATH $PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH

RUN curl https://pyenv.run | bash

# Install and use a specific Python version through pyenv
RUN pyenv install 3.13.7 && \
    pyenv global 3.13.7

WORKDIR /app

RUN pip install --upgrade pip

# Core ML/AI packages
RUN pip install numpy torch pandas scikit-learn \
    transformers xgboost lightgbm catboost \
    tensorflow keras

# Data processing & utilities
RUN pip install scipy statsmodels arch prophet \
    tslearn pyts tsfresh feature-engine \
    category-encoders

# Time series specific packages
RUN pip install darts prophet sktime

# Development & testing
RUN pip install pytest black flake8 pylint mypy

# System & network
RUN pip install httpx requests aiohttp docker redis \
    psycopg2-binary sqlalchemy

CMD ["tail", "-f", "/dev/null"]