from flask import Flask, render_template, request
import dhlab as dh
from dataclasses import dataclass, asdict
import urllib.parse
import html
from typing import Self
from functools import lru_cache
#from flask_cors import cross_origin
#from pydantic_settings import BaseSettings
            
@dataclass(frozen=True) #frozen=True so the dataclass becomes immutable and we can cache it later 
class CorpusMetadata:
    doc_type_selection: str | None = None
    language: str | None = None
    author: str | None = None
    title: str | None = None
    words_or_phrases: str | None = None
    key_words: str | None = None
    dewey: str | None = None
    from_year: str | None = None
    to_year: str | None = None
    search_type: str | None = None
    num_docs: str | None = None
    corpus_name: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> Self:
        return cls(
            doc_type_selection=data.get("doc_type_selection"),
            language=data.get("language"),
            author=data.get("author"),
            title=data.get("title"),
            words_or_phrases=data.get("words_or_phrases"),
            key_words=data.get("key_words"),
            dewey=data.get("dewey"),
            from_year=data.get("from_year"),
            to_year=data.get("to_year"),
            search_type=data.get("search_type"),
            num_docs=data.get("num_docs"),
            corpus_name=data.get("corpus_name")
        )

    def urlencode(self) -> str:
        data = {k: v for k, v in asdict(self).items() if v is not None}
        return html.escape(urllib.parse.urlencode(data))


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

@lru_cache
def create_corpus(metadata: CorpusMetadata) -> tuple[dh.Corpus, str]:
    dh_corpus_object = dh.Corpus(
        doctype=metadata.doc_type_selection,
        author=metadata.author,
        freetext=None,
        fulltext=metadata.words_or_phrases,
        from_year=metadata.from_year,
        to_year=metadata.to_year,
        from_timestamp=None,
        title=metadata.title,
        ddk=metadata.dewey,
        subject=metadata.key_words,
        lang=metadata.language,
        limit=metadata.num_docs,
        order_by=metadata.search_type,
        allow_duplicates=False,
    )
    
    
    return dh_corpus_object, metadata.doc_type_selection


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
        print("Form data received:", request.form)
        corpus_metadata = CorpusMetadata.from_dict(request.form)
        
        corpus, doctype = create_corpus(corpus_metadata)
        
        df_from_corpus = corpus.frame[CORPUS_COLUMNS[doctype]]
        
        json_table = df_from_corpus.to_json(orient="records")
        
        return render_template(
            "table.html",
            json_table=json_table,
            corpus_name_=corpus_metadata.corpus_name,
            res_table=df_from_corpus.to_html(table_id="results_table", border=0),
        )

    return app


app = create_app()

if __name__ == "__main__":
    app.run()