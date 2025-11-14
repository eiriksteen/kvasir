FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install ML/AI, Data Science, Time Series, and NLP Python packages
RUN pip install --no-cache-dir \
    numpy \
    pandas \
    scipy \
    matplotlib \
    seaborn \
    plotly \
    scikit-learn \
    xgboost \
    lightgbm \
    statsmodels \
    prophet \
    pmdarima \
    sktime \
    torch \
    torchvision \
    transformers \
    datasets \
    nltk \
    spacy \
    gensim \
    sentencepiece \
    tokenizers \
    pillow \
    scikit-image \
    opencv-python-headless \
    requests \
    tqdm \
    jupyter \
    ipython \
    pyarrow \
    fastparquet \
    openpyxl

CMD ["/bin/bash"]

