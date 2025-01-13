from dataclasses import dataclass
from functools import lru_cache
from typing import Self

import dhlab as dh  # type: ignore
from flask import Flask, render_template, request


def create_app() -> Flask:
    app = Flask(__name__)

    @app.route("/")
    def index() -> str:
        return render_template(
            "index_base.html",
            app_title="Korpusbygger",
            app_name="Korpusbygger",
        )

    @app.route("/submit-form", methods=["POST"])
    def make_corpus() -> str:
        corpus_metadata = CorpusMetadata.from_dict(request.form)

        corpus = create_corpus(corpus_metadata)
        df_from_corpus = corpus.frame[CORPUS_COLUMNS[corpus_metadata.document_type]]

        json_table = df_from_corpus.to_json(orient="records")  # type: ignore
        return render_template(
            "table.html",
            json_table=json_table,
            corpus_name_=corpus_metadata.corpus_name,
            res_table=df_from_corpus.to_html(table_id="results_table", border=0),  # type: ignore
        )

    return app


@dataclass(frozen=True)
class CorpusMetadata:
    document_type: str
    language: str | None
    author: str | None
    title: str | None
    words_or_phrases: str | None
    key_words: str | None
    dewey: str | None
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
            from_year=data.get("from_year"),
            to_year=data.get("to_year"),
            search_type=data.get("search_type", "random"),
            num_docs=int(data.get("num_docs", 2000)),
            corpus_name=data.get("corpus_name"),
        )


@lru_cache
def create_corpus(corpus_metadata: CorpusMetadata) -> dh.Corpus:
    dh_corpus_object = dh.Corpus(
        doctype=corpus_metadata.document_type,
        author=corpus_metadata.author,
        freetext=None,
        fulltext=corpus_metadata.words_or_phrases,
        from_year=corpus_metadata.from_year,
        to_year=corpus_metadata.to_year,
        from_timestamp=None,
        title=corpus_metadata.title,
        ddk=corpus_metadata.dewey,
        subject=corpus_metadata.key_words,
        lang=corpus_metadata.language,
        limit=corpus_metadata.num_docs,
        order_by=corpus_metadata.search_type,
        allow_duplicates=False,
    )

    return dh_corpus_object


CORPUS_COLUMNS: dict[str, list[str]] = {
    "digibok": [
        "dhlabid",
        "urn",
        "authors",
        "title",
        "city",
        "timestamp",
        "year",
        "publisher",
        "ddc",
        "subjects",
        "langs",
    ],
    "digavis": ["dhlabid", "urn", "authors", "title", "city", "timestamp", "year"],
    "digitidsskrift": [
        "dhlabid",
        "urn",
        "title",
        "city",
        "timestamp",
        "year",
        "publisher",
        "ddc",
        "subjects",
        "langs",
    ],
    "digistorting": ["dhlabid", "urn", "year"],
    "digimanus": ["dhlabid", "urn", "authors", "title", "timestamp", "year"],
    "kudos": [
        "dhlabid",
        "urn",
        "authors",
        "title",
        "timestamp",
        "year",
        "publisher",
        "langs",
    ],
    "nettavis": [
        "dhlabid",
        "urn",
        "title",
        "city",
        "timestamp",
        "year",
        "publisher",
        "langs",
    ],
}


app = create_app()

if __name__ == "__main__":
    app.run()
