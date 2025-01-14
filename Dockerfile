FROM python:3.12-slim-bookworm

COPY src/dhlab_corpus_webapp/ .
WORKDIR /app

RUN pip install --upgrade pip && pip uv sync && uv sync

EXPOSE 8080

CMD ["uv", "run", "gunicorn", "corpus_webapp", "--host", "0.0.0.0", "--port", "5000"]