import os
from datetime import datetime

from functools import lru_cache
from dataclasses import dataclass, asdict
from typing import Self
import zipfile

import flask
import pandas as pd
import dhlab as dhlab
import dhlab.api.dhlab_api as dhlab_api
from flask import render_template


@dataclass(frozen=True)
class CorpusMetadata:
    document_type: str
    language: str | None
    author: str | None
    title: str | None
    words_or_phrases: str | None
    key_words: str | None
    dewey: str | None
    subject: str | None
    from_year: str | None
    to_year: str | None
    search_type: str
    num_docs: int
    corpus_name: str

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> Self:
        return cls(
            document_type=data.get("doc_type_selection"),
            language=data.get("language"),
            author=data.get("author"),
            title=data.get("title"),
            words_or_phrases=data.get("words_or_phrases"),
            key_words=data.get("key_words"),
            dewey=data.get("dewey"),
            subject=data.get("subject"),
            from_year=data.get("from_year"),
            to_year=data.get("to_year"),
            search_type=data.get("search_type", "random"),
            num_docs=int(data.get("num_docs", 2000)),
            corpus_name=data.get("corpus_name"),
        )


corpus_cache_size = int(os.environ.get("DHLAB_CORPUS_CACHE_SIZE", 64))


@lru_cache(maxsize=corpus_cache_size)
def create_corpus(corpus_metadata: CorpusMetadata) -> pd.DataFrame:
    dh_corpus_object = dhlab_api.document_corpus(
        doctype=corpus_metadata.document_type,
        author=corpus_metadata.author,
        freetext=None,
        fulltext=corpus_metadata.words_or_phrases,
        from_year=corpus_metadata.from_year,
        to_year=corpus_metadata.to_year,
        from_timestamp=None,
        title=corpus_metadata.title,
        ddk=corpus_metadata.dewey,
        subject=corpus_metadata.subject,
        lang=corpus_metadata.language,
        limit=corpus_metadata.num_docs,
        order_by=corpus_metadata.search_type,
    )

    return dh_corpus_object


def spreadsheet_to_corpus(file) -> pd.DataFrame:
    if file.filename.endswith(".csv"):
        df = pd.read_csv(file)

    elif file.filename.endswith(".xls") or file.filename.endswith(".xlsx"):
        df = pd.read_excel(file)

    elif file.filename.endswith(".zip"):
        with zipfile.ZipFile(file, "r") as zf:
            corpus_file = zipfile.Path(zf) / "korpus.xlsx"
            if not corpus_file.exists():
                raise ValueError("ZipFile doesn't contain a corpus")

            df = pd.read_excel(corpus_file.open("rb"))

    urn_list = df["urn"].dropna().tolist()

    corpus = dhlab.Corpus()
    corpus.extend_from_identifiers(list(urn_list))
    return corpus.frame


def get_corpus_from_request(request: flask.Request) -> tuple[pd.DataFrame, str]:
    if request.files:
        corpus = spreadsheet_to_corpus(request.files["spreadsheet"])
        corpus_definition = {}
    else:
        corpus_metadata = CorpusMetadata.from_dict(request.form)
        corpus = create_corpus(corpus_metadata)
        corpus_definition = {k: repr(v) for k, v in asdict(corpus_metadata).items()}

    readme = render_template(
        "corpus_readme.md", corpus_definition=corpus_definition, timestamp=datetime.now().isoformat()
    )
    return corpus, readme
