FROM python:3.13-slim-trixie

WORKDIR /app

RUN pip install --upgrade pip && pip install uv
COPY src /app/src
COPY pyproject.toml /app/pyproject.toml
COPY README.md /app/README.md

RUN uv sync --no-dev --compile-bytecode

EXPOSE 5002

CMD ["uv", "run", "--no-sync", "gunicorn", "--bind", "0.0.0.0:5002", "dhlab_corpus_webapp.app:app"]
