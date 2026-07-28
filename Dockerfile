FROM python:3.14-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY app ./app

EXPOSE 8880

CMD ["uv", "run", "--no-sync", "uvicorn", "app.api_regles.main:app", "--host", "0.0.0.0", "--port", "8880"]
