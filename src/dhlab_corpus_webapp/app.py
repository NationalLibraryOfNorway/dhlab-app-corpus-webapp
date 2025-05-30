from functools import lru_cache
from flask import Flask, render_template, request, session
from dataclasses import dataclass, asdict
import dhlab as dh
import dhlab.api.dhlab_api as dhlab_api
import dhlab.text.conc_coll as cc
import pandas as pd
from flask_cors import cross_origin
from flask_cors import CORS
import dhlab.text.conc_coll as conc_coll
import jinja_partials
from typing import Self
from wordcloud import WordCloud
import matplotlib
matplotlib.use("agg")  # We must set the backend before importing pyplot
import matplotlib.pyplot as plt
import io
import base64
from whitenoise import WhiteNoise
import os
from pathlib import Path


ROOT_PATH = os.environ.get("ROOT_PATH", "")

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
    
    @app.route(f"{ROOT_PATH}/corpus-method", methods=['GET', 'POST'])
    @cross_origin() 
    def corpus_method() -> str:
        type_ = request.args.get("type_")
        if type_ == "build_corpus":
            return render_template("corpus_builder.html")
        elif type_ == "upload_corpus":
            return render_template("corpus_uploader.html")
        else:
            raise ValueError(f"Unknown corpus method: {type_}")

    @app.route(f"{ROOT_PATH}/submit-form", methods=['GET', 'POST'])
    @cross_origin() 
    def make_corpus() -> str:
        if request.files:
            uploaded_file = request.files['spreadsheet']

            corpus = speadsheet_to_corpus(uploaded_file)

            session['urn_list'] = corpus['urn'].tolist()

            corpus = corpus.frame

        else:
            corpus_metadata = CorpusMetadata.from_dict(request.form)
            
            session['corpus_metadata'] = asdict(corpus_metadata)
            
            corpus = create_corpus(corpus_metadata)

        return render_template(
            "table.html",
            res_table=corpus.to_html(table_id="results_table", border=0),
        )

    @app.route(f"{ROOT_PATH}/search-form-action")
    @cross_origin() 
    def choose_action() -> str:
        type_ = request.args.get("type_")

        if type_ == "show-corpus-table":
            corpus = get_corpus_from_session()

            doctype = corpus["doctype"].iloc[0]

            return render_template(
            "table.html",
            res_table=corpus.frame.to_html(table_id="results_table", border=0),
        )

        elif type_ == "search-collocation":
            return render_template("search-collocation.html")
        elif type_ == "search-concordance":
            return render_template("search-concordance.html")
        else:
            raise ValueError(f"Unknown action: {type_}")
    
    @app.route(f"{ROOT_PATH}/search_concordance")
    @cross_origin()
    def search_concordances() -> str:
        
        corpus = get_corpus_from_session()

        query = request.args.get("search")
        window = int(request.args.get("window", 20))
        #concordances = conc_coll.Concordance(corpus, query, limit=10, window=window)
        concordances = cc.Concordance(corpus, query, limit=10, window=window)

        resultframe = process_concordance_results(concordances, corpus)
        
        return jinja_partials.render_partial(
            "concordance_results.html",
            resultframe=resultframe
        )
    
    @app.route(f"{ROOT_PATH}/search_collocation")
    @cross_origin()
    def search_collocations() -> str:

        corpus = get_corpus_from_session()
        words = request.args.get("search")
        words_before = request.args.get("words_before", 10)
        words_after = request.args.get("words_after", 10)
        reference_corp = request.args.get("ref_korpus", 10)
        max_coll = request.args.get("max_coll")
        sorting_method = request.args.get("sorting_method")
        reference_path = f"reference/{reference_corp}"
        reference = read_csv(reference_path)
        
        #coll = corpus.coll(words=words, before=int(words_before), after=int(words_after), samplesize=1000, reference=reference)
        coll = cc.Collocations(corpus["urn"], words=words, before=int(words_before), after=int(words_after), samplesize=1000, reference=reference)
        coll_selected = coll.frame.sort_values(ascending=False, by=sorting_method)
        resultframe = coll_selected.head(int(max_coll))

        wordcloud_image = make_wordcloud(resultframe)
        
        return render_template(
            "collocation_results.html",
            resultframe=resultframe,
            wordcloud_image=wordcloud_image
        )

    return app

def read_csv(reference_path) -> pd.DataFrame:
    try:
        reference_df = pd.read_csv(reference_path)
        reference_df.columns = ["word", "freq"]
        reference = reference_df.set_index("word")
    except:
        print("Statisk referansekorpus kunne ikke hentes. Se på parametrene for korpuset eller prøv igjen.")

    return reference

def get_corpus_from_session() -> dh.Corpus:
    if 'urn_list' in session:
        corpus = dh.Corpus()
        corpus.extend_from_identifiers(session['urn_list'])
    elif 'corpus_metadata' in session:
        corpus_metadata = CorpusMetadata(**session['corpus_metadata'])
        corpus = create_corpus(corpus_metadata)
    else:
        raise ValueError("No corpus data found in session")
    
    return corpus

def process_concordance_results(concordances, corpus):
    def get_timeformat(df: pd.DataFrame) -> list[str]:
        return [
            "%Y-%m-%d" if doctype == "digavis" else "%Y"
            for doctype in df["doctype"]
        ]

    def get_timestamp(df: pd.DataFrame) -> pd.Series:
        return pd.to_datetime(
            df["timestamp"].astype(str), 
            format="%Y%m%d", 
            errors="coerce"
        ).fillna(pd.Timestamp('1900-01-01'))

    return pd.merge(
        concordances.frame, 
        corpus, 
        on="urn", 
        how="left"
    ).assign(
        timeformat=get_timeformat,
        timestamp=get_timestamp
    )[[
        "title",
        "authors",
        "year",
        "timestamp",
        "timeformat",
        "concordance",
        "link",
    ]]

def make_wordcloud(df, width=800, height=400, background_color='white'): 

    index_series = df.index.to_series()
    words = index_series.str.replace(r'\s+\d+$', '', regex=True)
    word_freq = dict(zip(words, df['relevance']))
    
    wc = WordCloud(width=width, 
                  height=height, 
                  background_color=background_color,
                  max_words=100)
    
    wc.generate_from_frequencies(word_freq)
    
    img = io.BytesIO()
    plt.figure(figsize=(10, 5))
    plt.imshow(wc, interpolation='bilinear')
    plt.axis('off')
    plt.savefig(img, format='png', bbox_inches='tight', pad_inches=0)
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
def create_corpus(corpus_metadata: CorpusMetadata) -> dh.Corpus:
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
        order_by=corpus_metadata.search_type
    )

    return dh_corpus_object


def speadsheet_to_corpus(file) -> dh.Corpus:
    
    if file.filename.endswith('.csv'):
        df = pd.read_csv(file)

    elif file.filename.endswith('.xls') or file.filename.endswith('.xlsx'):
        df = pd.read_excel(file)
    urn_list = df["urn"].dropna().tolist() 
    
    return urn_list_to_corpus(tuple(urn_list))


@lru_cache
def urn_list_to_corpus(urn_list: tuple[str]) -> dh.Corpus:
    corpus = dh.Corpus()
    corpus.extend_from_identifiers(list(urn_list))
    return corpus


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
    "tidlig nynorsk (før 1875)": "reference/nob_1848_1875.csv"
}

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5009)
