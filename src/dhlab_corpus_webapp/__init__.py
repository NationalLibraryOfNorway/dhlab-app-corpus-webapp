from functools import lru_cache
from pathlib import Path

import dhlab.api.dhlab_api as dhlab_api
import dhlab.text.conc_coll as conc_coll
import httpx
import jinja_partials
import pandas as pd
from flask import Flask, render_template, request
from flask_cors import cross_origin
from pydantic_settings import BaseSettings

class Config(BaseSettings):
    ROOT_PATH: str = ""  # This should be "/run" on GCP


doctypes = {
    "Alle dokumenter": "all",
    "Aviser": "digavis",
    "Bøker": "digibok",
    "Brev og manuskripter": "digimanus",
    "Tidsskrift": "digitidsskrift",
    "Stortingsdokumenter": "digistorting",
    "Nettarkiv (helsekorpus)": "SNOMED*",
}


def parse_response(response: httpx.Response) -> None:
    pass


@lru_cache
def get_corpus(
    doctype: str = "digibok",
    from_year: int = 1990,
    to_year: int = 2020,
    limit: int = 1000,
    freetext: str = None,
    fulltext: str = None,
) -> list[str]:
    if doctype == "SNOMED*":
        corpus = dhlab_api.document_corpus(
            doctype=doctype, limit=limit, freetext=freetext, fulltext=fulltext
        )
    else:
        corpus = dhlab_api.document_corpus(
            doctype=doctype,
            from_year=from_year,
            to_year=to_year,
            limit=limit,
            freetext=freetext,
            fulltext=fulltext,
        )

    return corpus


def create_app() -> Flask:
    config = Config()
    app = Flask(__name__)
    jinja_partials.register_extensions(app)
    static_root_path = Path(__file__).parent / "static"

    @app.route("/")
    @cross_origin()  # This is needed since the traffic is routed via "dh.nb.no/run/{appname}" not directly to the GCP server
    def home() -> str:
        return render_template(
            "corpus.html",
            app_title="NB DH-LAB – Korpus",
            app_name="Korpus",
        )

    @app.route("/search_concordance")
    @cross_origin()  # This is needed since the traffic is routed via "dh.nb.no/run/{appname}" not directly to the GCP server
    def search_concordances() -> str:
        corpus = get_corpus(doctype="digavis")
        query = request.args.get("search")
        window = request.args.get("window", 20)
        concordances = conc_coll.Concordance(corpus, query, limit=10, window=window)

        def get_timeformat(df: pd.DataFrame) -> list[str]:
            return [
                "%Y-%m-%d" if doctype == "digavis" else "%Y"
                for doctype in df["doctype"]
            ]

        def get_timestamp(df: pd.DataFrame) -> pd.Series:
            return pd.to_datetime(
                df["timestamp"].astype(str), format="%Y%m%d", errors="coerce"
            )

        resultframe = pd.merge(concordances.frame, corpus, on="urn", how="left").assign(
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
        return jinja_partials.render_partial(
            "partials/concordance_results.html",
            resultframe=resultframe,
        )

    # Serve all static paths, needed for deployment on GCP since we need to add the root path
    for path in static_root_path.iterdir():
        if path.is_file():
            app.add_url_rule(
                f"{config.ROOT_PATH}/{path.name}",
                f"{path.name}",
                view_func=lambda path=path: app.send_static_file(path.name),
            )

    @app.route("/corpus-method")
    @cross_origin()  # This is needed since the traffic is routed via "dh.nb.no/run/{appname}" not directly to the GCP server
    def corpus_method() -> str:
        type_ = request.args.get("type_")
        if type_ == "build_corpus":
            return render_template("partials/corpus_builder.html")
        elif type_ == "upload_corpus":
            return render_template("partials/corpus_uploader.html")
        else:
            raise ValueError(f"Unknown corpus method: {type_}")

    return app



app = create_app()

if __name__ == "__main__":
    app.run()