FROM python:3.12-slim-bookworm

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY src /app/src
COPY pyproject.toml .
COPY README.md .

RUN pip install --upgrade pip \
&& pip install uv

RUN uv sync

WORKDIR /app/src/dhlab_corpus_webapp

EXPOSE 5000

CMD ["uv", "run", "gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
