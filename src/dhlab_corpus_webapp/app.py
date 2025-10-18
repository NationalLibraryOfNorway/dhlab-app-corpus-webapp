import base64
import io
import os
from functools import lru_cache
from dataclasses import dataclass
from pathlib import Path
from typing import Self

import flask
import pandas as pd
import dhlab as dhlab
import dhlab.api.dhlab_api as dhlab_api
import dhlab.text.conc_coll
import jinja_partials
from flask import Flask, render_template, request
from flask_cors import cross_origin
from whitenoise import WhiteNoise
from wordcloud import WordCloud


ROOT_PATH = os.environ.get("ROOT_PATH", "")
REFERENCE_PATH = Path(__file__).parent / "reference"
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
REFERENCES = {
    "generisk referanse (1800-2022)": "reference/nob-nno_1800_2022.csv",
    "nåtidig bokmål (2000-)": "reference/nob_2000_2022.csv",
    "nåtidig nynorsk (2000-)": "reference/nno_2000_2022.csv",
    "bokmål (1950-2000)": "reference/nob_1950_2000.csv",
    "nynorsk (1950-2000)": "reference/nno_1950_2000.csv",
    "bokmål (1920-1950)": "reference/nob_1920_1950.csv",
    "nynorsk (1920-1950)": "reference/nno_1920_1950.csv",
    "bokmål (1875-1920)": "reference/nob_1875_1920.csv",
    "nynorsk (1875-1920)": "reference/nno_1875_1920.csv",
    "tidlig dansk-norsk/bokmål (før 1875)": "reference/nob_1800_1875.csv",
    "tidlig nynorsk (før 1875)": "reference/nob_1848_1875.csv",
}


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


@lru_cache
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


@lru_cache
def urn_list_to_corpus(urn_list: tuple[str]) -> pd.DataFrame:
    corpus = dhlab.Corpus()
    corpus.extend_from_identifiers(list(urn_list))
    return corpus.frame


def spreadsheet_to_corpus(file) -> pd.DataFrame:
    if file.filename.endswith(".csv"):
        df = pd.read_csv(file)

    elif file.filename.endswith(".xls") or file.filename.endswith(".xlsx"):
        df = pd.read_excel(file)
    urn_list = df["urn"].dropna().tolist()

    return urn_list_to_corpus(tuple(urn_list))


def process_concordance_results(concordances: pd.DataFrame, corpus: pd.DataFrame) -> pd.DataFrame:
    def get_timeformat(df: pd.DataFrame) -> list[str]:
        return ["%Y-%m-%d" if doctype == "digavis" else "%Y" for doctype in df["doctype"]]

    def get_timestamp(df: pd.DataFrame) -> pd.Series:
        timestamps = pd.to_datetime(df["timestamp"].astype(str), format="%Y%m%d", errors="coerce")
        return timestamps.fillna(pd.Timestamp("1900-01-01"))

    columns = [
        "title",
        "authors",
        "year",
        "timestamp",
        "timeformat",
        "concordance",
        "link",
    ]
    return pd.merge(concordances, corpus, on="urn", how="left").assign(
        timeformat=get_timeformat, timestamp=get_timestamp
    )[columns]


def make_wordcloud(df: pd.DataFrame) -> str:
    index_series = df.index.to_series()
    words = index_series.str.replace(r"\s+\d+$", "", regex=True)
    word_freq = dict(zip(words, df["relevance"]))

    wc = WordCloud(width=800, height=400, background_color="white", max_words=100)
    wc.generate_from_frequencies(word_freq)

    img = io.BytesIO()
    wc.to_image().save(img, format="PNG")

    img.seek(0)
    img_str = base64.b64encode(img.getvalue()).decode()

    return img_str


def get_corpus_from_request(request: flask.Request) -> pd.DataFrame:
    if request.files:
        uploaded_file = request.files["spreadsheet"]
        return spreadsheet_to_corpus(uploaded_file)
    else:
        corpus_metadata = CorpusMetadata.from_dict(request.form)
        return create_corpus(corpus_metadata)


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = "superhemmelig-noekkel"
    static_root_path = Path(__file__).parent / "static"
    app.wsgi_app = WhiteNoise(app.wsgi_app, root=static_root_path, prefix=ROOT_PATH)

    @app.route(f"{ROOT_PATH}/")
    @cross_origin()
    def index() -> str:
        return render_template(
            "index_base.html",
            app_title="Korpus | Konkordanser | Kollokasjoner",
            app_name="Korpus | Konkordanser | Kollokasjoner",
        )

    @app.route(f"{ROOT_PATH}/choose-action", methods=["GET"])
    @cross_origin()
    def choose_action() -> str | flask.Response:
        selected_option = request.args.get("type_")
        if selected_option == "build_corpus":
            return render_template("corpus_builder.html")
        elif selected_option == "make_coll":
            return render_template("search-collocation.html")
        elif selected_option == "make_conc":
            return render_template("search-concordance.html")
        else:
            return flask.Response("Invalid option", status=400)

    @app.route(f"{ROOT_PATH}/submit-form", methods=["GET", "POST"])
    @cross_origin()
    def make_corpus() -> str:
        corpus: pd.DataFrame = get_corpus_from_request(request)

        # We need to get the document type from the corpus itself as the user may have uploaded their own corpus
        doctype = corpus["doctype"].unique().item()
        selected_columns = corpus[CORPUS_COLUMNS[doctype]]
        return render_template(
            "table.html",
            json_table=corpus.to_json(orient="records"),
            res_table=selected_columns.to_html(table_id="results_table", border=0),
        )

    @app.route(f"{ROOT_PATH}/search_concordance", methods=["POST"])
    @cross_origin()
    def search_concordances() -> str:
        corpus = get_corpus_from_request(request)
        concordances = dhlab.text.conc_coll.Concordance(
            corpus,
            query=request.form.get("search"),
            limit=20,
            window=int(request.args.get("window", 20)),
        ).frame

        return jinja_partials.render_partial(
            "concordance_results.html",
            resultframe=process_concordance_results(concordances, corpus),
        )

    @app.route(f"{ROOT_PATH}/search_collocation", methods=["POST"])
    @cross_origin()
    def search_collocations() -> str:
        corpus = get_corpus_from_request(request)

        reference_path = REFERENCE_PATH / request.form.get("ref_korpus")
        reference = pd.read_csv(reference_path, index_col=0, header=None, names=["word", "freq"])

        coll = dhlab.text.conc_coll.Collocations(
            corpus["urn"],
            words=request.form.get("search"),
            before=int(request.form.get("words_before", 10)),
            after=int(request.form.get("words_after", 10)),
            samplesize=1000,
            reference=reference,
        ).frame

        sorting_method = request.form.get("sorting_method")
        coll_selected = coll.dropna().sort_values(ascending=False, by=sorting_method)

        max_coll = int(request.form.get("max_coll"))
        resultframe = coll_selected.head(max_coll)
        wordcloud_image = make_wordcloud(resultframe)

        return render_template(
            "collocation_results.html",
            resultframe=resultframe,
            wordcloud_image=wordcloud_image,
            order_by=sorting_method,
        )

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5009)
