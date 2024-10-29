# DH-Lab korpusbygger

## Installasjonsinstrukser

Vi bruker [uv](https://docs.astral.sh/uv/) for å håndtere pythonmiljø og avhengigheter. Installer det med *[Standalone installer](https://docs.astral.sh/uv/getting-started/installation/#standalone-installer)*.

Deretter kan du installere denne pakken ved å kjøre `uv sync` i mappen du klonet.

### Pre-commit

Skru på pre-commit for å passe på at alle commits følger standardene ved å kjøre følgende kommando i rotmappa til prosjektet:

```raw
pre-commit install
```

Hvis du ikke har Pre-commit installert kan du bruke uv til å installere det:

```raw
uv tool install pre-commit
```

### Starte webappen med uv

For å starte webappen i utviklermodus med flask, kjør

```raw
uv run flask --app dhlab_corpus_webapp.app run
```

Tilsvarende, for å starte webappen med gunicorn (f.eks. for deployments), kjør

```raw
uv run gunicorn dhlab_corpus_webapp.app:app run
```
