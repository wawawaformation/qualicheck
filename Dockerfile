FROM python:3.14-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY app ./app

# Fige le commit dans l'image (endpoint /version) : pas dans .env, pour
# garantir que la valeur reflete le code reellement compile dans cette
# image, pas une config de deploiement qui pourrait diverger.
ARG GIT_SHA=inconnu
ENV GIT_SHA=$GIT_SHA

EXPOSE 8880

CMD ["uv", "run", "--no-sync", "uvicorn", "app.api_regles.main:app", "--host", "0.0.0.0", "--port", "8880"]
