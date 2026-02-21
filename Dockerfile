# Use imagem Python 3.12
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TORCH_HOME=/app/models \
    TRANSFORMERS_CACHE=/app/models

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies em stages para otimizar
RUN pip install --upgrade pip setuptools wheel

# Instalar dependências básicas primeiro
RUN pip install \
    Django>=6.0 \
    python-dotenv>=1.0.0 \
    requests>=2.31.0 \
    gunicorn>=23.0.0 \
    psycopg2-binary>=2.9.0 \
    dj-database-url>=3.0.0 \
    Pillow>=11.0.0 \
    whitenoise>=6.5.0

# Depois instalar LangChain/LangGraph
RUN pip install \
    langchain>=0.1.0 \
    langchain-core>=0.1.0 \
    langchain-openai>=0.1.0 \
    langchain-community>=0.0.10 \
    langgraph>=0.0.1

# Depois instalar dependências pesadas (SBERT)
RUN pip install \
    sentence-transformers>=2.2.0 \
    torch>=2.0.0 \
    transformers>=4.30.0 \
    numpy>=1.24.0 \
    tiktoken>=0.5.0 \
    protobuf>=3.20.0 \
    sentencepiece>=0.1.99

# Copy project
COPY . .

# Copy entrypoint
COPY docs/deploy/entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

# Create necessary directories
RUN mkdir -p mzkiInformatica/staticfiles mzkiInformatica/media logs models

# Expose port
EXPOSE 8000

# Run entrypoint
ENTRYPOINT ["/bin/bash", "docs/deploy/entrypoint.sh"]
