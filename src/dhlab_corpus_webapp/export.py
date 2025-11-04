import io
import zipfile

import pandas as pd
import dhlab as dhlab
from flask import render_template, request


def create_corpus_zipfile(corpus: pd.DataFrame, corpus_readme: str) -> io.BytesIO:
    download_stream = io.BytesIO()
    download_stream.filename = ":memory:"
    with zipfile.ZipFile(download_stream, mode="w") as zf:
        zip_path = zipfile.Path(zf)

        corpus.to_excel((zip_path / "korpus.xlsx").open("wb"), sheet_name="Korpus")
        with (zip_path / "LESMEG_KORPUS.md").open("wt") as f:
            f.write(corpus_readme)

    download_stream.seek(0)
    return download_stream


def create_collocations_zipfile(
    corpus: pd.DataFrame, corpus_readme: str, collocations: pd.DataFrame, wordcloud_image: io.BytesIO
) -> io.BytesIO:
    download_stream = create_corpus_zipfile(corpus, corpus_readme)

    with zipfile.ZipFile(download_stream, "a") as zf:
        zip_path = zipfile.Path(zf)
        collocations.to_excel((zip_path / "kollokasjoner.xlsx").open("wb"), sheet_name="Kollokasjoner")

        with (zip_path / "ordsky.png").open("wb") as f:
            f.write(wordcloud_image.getvalue())

        with (zip_path / "LESMEG_KOLLOKASJONER.md").open("wt") as f:
            f.write(render_template("collocation_readme.md", form=request.form))

    download_stream.seek(0)
    return download_stream


def create_concordance_zipfile(corpus: pd.DataFrame, corpus_readme: str, concordances: pd.DataFrame) -> io.BytesIO:
    download_stream = create_corpus_zipfile(corpus, corpus_readme)
    with zipfile.ZipFile(download_stream, "a") as zf:
        zip_path = zipfile.Path(zf)
        concordances.to_excel((zip_path / "konkordanser.xlsx").open("wb"), sheet_name="Konkordanser", index=False)

    download_stream.seek(0)
    return download_stream
