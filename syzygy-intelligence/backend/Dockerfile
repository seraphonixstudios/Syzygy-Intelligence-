FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# Install in stages to avoid dependency backtracking
RUN pip install --no-cache-dir fastapi uvicorn[standard] pydantic pydantic-settings python-dotenv && \
    pip install --no-cache-dir sqlalchemy[asyncio] asyncpg alembic redis neo4j chromadb pgvector && \
    pip install --no-cache-dir sentence-transformers numpy playwright httpx aiofiles pyyaml && \
    pip install --no-cache-dir pyjwt passlib[bcrypt] python-multipart structlog networkx matplotlib Pillow && \
    pip install --no-cache-dir ollama openai && \
    pip install --no-cache-dir langgraph langgraph-checkpoint && \
    pip install --no-cache-dir litellm

RUN pip install --no-cache-dir psycopg2-binary

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
