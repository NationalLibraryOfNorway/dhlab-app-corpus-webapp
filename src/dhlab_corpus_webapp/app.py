import base64
import io
import os
from functools import lru_cache
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Self

import pandas as pd
import dhlab as dhlab
import dhlab.api.dhlab_api as dhlab_api
import dhlab.text.conc_coll
import jinja_partials
from flask import Flask, render_template, request, session
from flask_cors import cross_origin
from whitenoise import WhiteNoise
from wordcloud import WordCloud

# We import matplotlib separately since we need to set the backend before importing pyplot
import matplotlib

matplotlib.use("agg")
import matplotlib.pyplot as plt


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
    def choose_action():
        selected_option = request.args.get("type_")
        if selected_option == "build_corpus":
            return render_template("corpus_builder.html")
        elif selected_option == "make_coll":
            return render_template("search-collocation.html")
        elif selected_option == "make_conc":
            return render_template("search-concordance.html")
        else:
            return "Invalid option", 400

    @app.route(f"{ROOT_PATH}/submit-form", methods=["GET", "POST"])
    @cross_origin()
    def make_corpus() -> str:
        if request.files:
            uploaded_file = request.files["spreadsheet"]

            corpus = spreadsheet_to_corpus(uploaded_file)

            session["urn_list"] = corpus.frame["urn"].tolist()

        else:
            session.pop('urn_list', None)
            corpus_metadata = CorpusMetadata.from_dict(request.form)

            session["corpus_metadata"] = asdict(corpus_metadata)

            corpus = create_corpus(corpus_metadata)

        json_table = corpus.to_json(orient="records")
        doctype = corpus["doctype"].iloc[0]
        selected_columns = corpus[CORPUS_COLUMNS[doctype]]

        return render_template(
            "table.html",
            res_table=corpus.to_html(table_id="results_table", border=0),
        )

    @app.route(f"{ROOT_PATH}/search_concordance", methods=["POST"])
    @cross_origin()
    def search_concordances() -> str:
        uploaded_file = request.files["spreadsheet"]
        corpus = spreadsheet_to_corpus(uploaded_file)

        query = request.form.get("search")

        window = int(request.args.get("window", 20))

        concordances = dhlab.text.conc_coll.Concordance(
            corpus, query, limit=20, window=window
        )

        resultframe = process_concordance_results(concordances, corpus.frame)

        return jinja_partials.render_partial(
            "concordance_results.html", resultframe=resultframe
        )

    @app.route(f"{ROOT_PATH}/search_collocation", methods=["POST"])
    @cross_origin()
    def search_collocations() -> str:
        uploaded_file = request.files["spreadsheet"]

        corpus = spreadsheet_to_corpus(uploaded_file)

        session["urn_list"] = corpus.frame["urn"].tolist()

        words = request.form.get("search")
        words_before = request.form.get("words_before", 10)
        words_after = request.form.get("words_after", 10)
        reference_corp = request.form.get("ref_korpus")
        max_coll = request.form.get("max_coll")
        sorting_method = request.form.get("sorting_method")

        reference_path = REFERENCE_PATH / reference_corp
        reference = pd.read_csv(
            reference_path, index_col=0, header=None, names=["word", "freq"]
        )

        coll = dhlab.text.conc_coll.Collocations(
            corpus["urn"],
            words=words,
            before=int(words_before),
            after=int(words_after),
            samplesize=1000,
            reference=reference,
        )
        coll_selected = coll.frame.dropna().sort_values(
            ascending=False, by=sorting_method
        )

        resultframe = coll_selected.head(int(max_coll))

        wordcloud_image = make_wordcloud(resultframe)

        return render_template(
            "collocation_results.html",
            resultframe=resultframe,
            wordcloud_image=wordcloud_image,
            order_by=sorting_method,
        )

    return app


def process_concordance_results(concordances, corpus):
    def get_timeformat(df: pd.DataFrame) -> list[str]:
        return [
            "%Y-%m-%d" if doctype == "digavis" else "%Y" for doctype in df["doctype"]
        ]

    def get_timestamp(df: pd.DataFrame) -> pd.Series:
        return pd.to_datetime(
            df["timestamp"].astype(str), format="%Y%m%d", errors="coerce"
        ).fillna(pd.Timestamp("1900-01-01"))

    return pd.merge(concordances.frame, corpus, on="urn", how="left").assign(
        timeformat=get_timeformat, timestamp=get_timestamp
    )[
        [
            "title",
            "authors",
            "year",
            "timestamp",
            "timeformat",
            "concordance",
            "link",
        ]
    ]


def make_wordcloud(df, width=800, height=400, background_color="white"):
    index_series = df.index.to_series()
    words = index_series.str.replace(r"\s+\d+$", "", regex=True)
    word_freq = dict(zip(words, df["relevance"]))

    wc = WordCloud(
        width=width, height=height, background_color=background_color, max_words=100
    )

    wc.generate_from_frequencies(word_freq)

    img = io.BytesIO()
    plt.figure(figsize=(10, 5))
    plt.imshow(wc, interpolation="bilinear")
    plt.axis("off")
    plt.savefig(img, format="png", bbox_inches="tight", pad_inches=0)
    plt.close()

    img.seek(0)
    img_str = base64.b64encode(img.getvalue()).decode()

    return img_str


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
def create_corpus(corpus_metadata: CorpusMetadata) -> dhlab.Corpus:
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


def spreadsheet_to_corpus(file) -> dhlab.Corpus:
    if file.filename.endswith(".csv"):
        df = pd.read_csv(file)

    elif file.filename.endswith(".xls") or file.filename.endswith(".xlsx"):
        df = pd.read_excel(file)
    urn_list = df["urn"].dropna().tolist()

    return urn_list_to_corpus(tuple(urn_list))

#Funksjon som lager et korpus basert på urn-er når brukeren laster opp et regneark
@lru_cache
def urn_list_to_corpus(urn_list: tuple[str]) -> dhlab.Corpus:
    corpus = dhlab.Corpus()
    corpus.extend_from_identifiers(list(urn_list))
    return corpus.frame


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5009)
