import base64
import io
import json
import os
from pathlib import Path
from typing import NotRequired, TypedDict

import flask
import pandas as pd
import dhlab as dhlab
import dhlab.text.conc_coll
import jinja_partials
from flask import Flask, render_template, request
from flask_cors import cross_origin
from wordcloud import WordCloud

import dhlab_corpus_webapp.export
from dhlab_corpus_webapp.corpus import get_corpus_from_request

ROOT_PATH = os.environ.get("ROOT_PATH", "")
DATA_PATH = Path(__file__).parent / "static/data"
REFERENCE_PATH = DATA_PATH / "reference_corpora"
LANGUAGES = json.loads((DATA_PATH / "languages.json").read_text(encoding="utf-8"))
CORPUS_COLUMNS_FULL: dict[str, list[str]] = {
    "digibok": [
        "dhlabid",
        "urn",
        "title",
        "authors",
        "city",
        "timestamp",
        "year",
        "publisher",
        "ddc",
        "subjects",
        "langs",
    ],
    "digavis": ["dhlabid", "urn", "title", "city", "timestamp", "year"],
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
    "digistorting": ["dhlabid", "urn", "title", "year"],
    "digimanus": ["dhlabid", "urn", "title", "authors", "timestamp", "year"],
    "kudos": [
        "dhlabid",
        "urn",
        "title",
        "authors",
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
CORPUS_COLUMNS_MINIMAL: dict[str, list[str]] = {
    "digibok": ["authors", "title", "timestamp"],
    "digavis": ["title", "timestamp"],
    "digitidsskrift": ["title", "timestamp"],
    "digistorting": ["title", "timestamp"],
    "digimanus": ["authors", "title", "timestamp"],
    "kudos": ["authors", "title", "timestamp"],
    "nettavis": ["title", "timestamp"],
}
COLUMN_NAMES = {
    "urn": "URN",
    "authors": "Forfattere",
    "title": "Tittel",
    "city": "Sted",
    "timestamp": "Tidspunkt",
    "year": "År",
    "publisher": "Utgiver",
    "ddc": "Dewey",
    "subjects": "Emner",
    "langs": "Språk",
}

REFERENCES = {
    "Generisk referanse (1800-2022)": "nob-nno_1800_2022.csv",
    "Nåtidig bokmål (2000-)": "nob_2000_2022.csv",
    "Nåtidig nynorsk (2000-)": "nno_2000_2022.csv",
    "Bokmål (1950-2000)": "nob_1950_2000.csv",
    "Nynorsk (1950-2000)": "nno_1950_2000.csv",
    "Bokmål (1920-1950)": "nob_1920_1950.csv",
    "Nynorsk (1920-1950)": "nno_1920_1950.csv",
    "Bokmål (1875-1920)": "nob_1875_1920.csv",
    "Nynorsk (1875-1920)": "nno_1875_1920.csv",
    "Tidlig dansk-norsk/bokmål (før 1875)": "nob_1800_1875.csv",
    "Tidlig nynorsk (før 1875)": "nob_1848_1875.csv",
}


def parse_timestamp(corpus: pd.DataFrame) -> pd.DataFrame:
    def get_timeformat(df: pd.DataFrame) -> list[str]:
        return ["%d. %b %Y" if doctype == "digavis" else "%Y" for doctype in df["doctype"]]

    def get_timestamp(df: pd.DataFrame) -> pd.Series:
        timestamps = pd.to_datetime(df["timestamp"].astype(str), format="%Y%m%d", errors="coerce")
        return timestamps.fillna(pd.Timestamp("1900-01-01"))

    return corpus.assign(timeformat=get_timeformat, timestamp=get_timestamp)


def process_concordance_results(concordances: pd.DataFrame, corpus: pd.DataFrame) -> pd.DataFrame:
    return pd.merge(concordances, parse_timestamp(corpus), on="urn", how="left")


def make_wordcloud(df: pd.DataFrame) -> io.BytesIO:
    index_series = df.index.to_series()
    words = index_series.str.replace(r"\s+\d+$", "", regex=True)
    word_freq = dict(zip(words, df["relevance"]))

    wc = WordCloud(width=800, height=400, background_color="white", max_words=100)
    wc.generate_from_frequencies(word_freq)

    img_stream = io.BytesIO()
    wc.to_image().save(img_stream, format="PNG")

    img_stream.seek(0)
    return img_stream


class DataTablesColumnDef(TypedDict):
    target: int
    name: NotRequired[str]
    title: NotRequired[str]
    visible: NotRequired[bool]


def get_corpus_column_definitions(corpus: pd.DataFrame, doctype: str) -> list[DataTablesColumnDef]:
    return [
        {
            "target": i,
            "name": column,
            "title": COLUMN_NAMES.get(column, column),
            "visible": column in CORPUS_COLUMNS_MINIMAL[doctype],
        }
        for i, column in enumerate(corpus.columns)
    ]


def make_url(urn: str, title: str) -> str:
    """Turn title and URN into an URL

    If the title is missing, the URN is used as the anchor text. This fixes an issue where digistorting corpora
    doesn't have titles.
    """
    if not title:
        title = urn
    return f'<a href="https://www.nb.no/items/{urn}" target="_blank">{title}</a>'


def render_corpus_table_for_request(request: flask.Request) -> str:
    corpus, readme = get_corpus_from_request(request)
    download_stream = dhlab_corpus_webapp.export.create_corpus_zipfile(corpus, readme)

    # check for non-empty corpus, otherwise return empty table
    if len(corpus) > 0:
        doctypes = corpus["doctype"].unique()
        if not doctypes:
            doctype = "digibok"
        elif len(doctypes) > 1:
            return f"Feil: Korpustabell kan bare inneholde en dokumenttype. Ditt korpus inneholder {doctypes}", 406
        doctype = doctypes.item()

        corpus = parse_timestamp(corpus)
        corpus = corpus.assign(
            title=corpus.apply(lambda row: make_url(row.urn, row.title), axis="columns"),
            timestamp=corpus.apply(lambda row: row.timestamp.strftime(row.timeformat), axis="columns"),
        )[CORPUS_COLUMNS_FULL[doctype]]

        # prepare data and table
        corpus_html = corpus.to_html(table_id="results_table", classes=["display"], border=0, index=False, escape=False)
        data_zip = base64.b64encode(download_stream.getvalue()).decode("utf-8")
        column_definitions = json.dumps(get_corpus_column_definitions(corpus, doctype))
    else:
        corpus_html = None
        data_zip = None
        column_definitions = None

    return render_template(
        "outputs/table.html",
        res_table=corpus_html,
        data_zip=data_zip,
        column_definitions=column_definitions,
    )


def render_concordances_for_request(request: flask.Request) -> str:
    if (limit := int(request.form.get("limit"))) > 1000:
        return flask.Response(f"Limit too high, is {limit}, must be less than 1000", status=400)
    if (window := int(request.form.get("window"))) > 25:
        return flask.Response(f"Window is too large, is {window}, must be less than 25", status=400)
    query = request.form.get("search")

    corpus, corpus_readme = get_corpus_from_request(request)

    # check first if the corpus if emtpy, then no concordances are expected
    if len(corpus) > 0:
        doctypes = corpus["doctype"].unique()

        concordances = dhlab.text.conc_coll.Concordance(
            corpus, query=request.form.get("search"), limit=limit, window=window
        ).frame
    else:
        doctypes = None
        concordances = None

    # check if we got any concordances from the corpus
    if concordances is not None:
        processed_conc = process_concordance_results(concordances, corpus)
        download_stream = dhlab_corpus_webapp.export.create_concordance_zipfile(
            corpus=corpus, corpus_readme=corpus_readme, concordances=processed_conc
        )

        data_zip = base64.b64encode(download_stream.getvalue()).decode("utf-8")
    else:
        data_zip = None
        processed_conc = pd.DataFrame()

    return jinja_partials.render_partial(
        "outputs/concordance.html",
        concordances=processed_conc,
        data_zip=data_zip,
        query=query,
        doctypes=doctypes,
    )


def render_collocations_for_request(request: flask.Request) -> str:
    corpus, corpus_readme = get_corpus_from_request(request)

    # Load reference corpus
    reference_path = REFERENCE_PATH / REFERENCES.get(request.form.get("ref_korpus"))
    reference = pd.read_csv(reference_path, index_col=0, header=None, names=["word", "freq"])

    # Create collocations dataframe sorted by the specified method
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

    # Truncate results and create wordcloud
    max_coll = int(request.form.get("max_coll"))
    resultframe = coll_selected.head(max_coll)
    wordcloud_image = make_wordcloud(resultframe)

    # Setup collocations zip file
    download_stream = dhlab_corpus_webapp.export.create_collocations_zipfile(
        corpus, corpus_readme, resultframe, wordcloud_image
    )

    return render_template(
        "outputs/collocations.html",
        resultframe=resultframe,
        wordcloud_image=base64.b64encode(wordcloud_image.getvalue()).decode("utf-8"),
        order_by=sorting_method,
        data_zip=base64.b64encode(download_stream.getvalue()).decode("utf-8"),
    )


def create_app() -> Flask:
    app = Flask(__name__)

    @app.route(f"{ROOT_PATH}/")
    @app.route(f"{ROOT_PATH}/index.html")
    @cross_origin()
    def index() -> str:
        return render_template(
            "index.html",
            languages=LANGUAGES,
            app_name="Korpusutforsker",
            banner_link_url="readme.html",
            banner_link_text="Om appen",
        )

    @app.route(f"{ROOT_PATH}/readme.html")
    @cross_origin()
    def readme() -> str:
        return render_template(
            "readme.html",
            app_name="Korpusutforsker",
            banner_link_url="index.html",
            banner_link_text="Tilbake til appen",
        )

    @app.route(f"{ROOT_PATH}/corpus-definition-method", methods=["GET"])
    @cross_origin()
    def corpus_definition_method() -> str:
        if request.args.get("corpus-builder-method") == "upload_corpus":
            return render_template("corpus_definition/upload_corpus.html")

        return render_template("corpus_definition/build_corpus.html", languages=LANGUAGES)

    @app.route(f"{ROOT_PATH}/exploration-method", methods=["GET"])
    @cross_origin()
    def exploration_method() -> str | flask.Response:
        selected_option = request.args.get("method")
        if selected_option == "table":
            return render_template("exploration_methods/table.html")
        elif selected_option == "collocations":
            return render_template("exploration_methods/collocations.html", reference_corpora=REFERENCES)
        elif selected_option == "concordance":
            return render_template("exploration_methods/concordance.html")
        else:
            return flask.Response(f"Invalid exploration method {selected_option}", status=400)

    @app.route(f"{ROOT_PATH}/explore", methods=["POST"])
    @cross_origin()
    def explore_corpus() -> str:
        exploration_method = request.form.get("exploration-method")

        if exploration_method == "table":
            return render_corpus_table_for_request(request)
        elif exploration_method == "collocations":
            return render_collocations_for_request(request)
        elif exploration_method == "concordance":
            return render_concordances_for_request(request)
        else:
            return flask.Response(f"Invalid exploration method: {exploration_method}", status=400)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5010)
