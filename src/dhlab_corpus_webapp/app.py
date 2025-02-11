from functools import lru_cache
from flask import Flask, render_template, request, session
from dataclasses import dataclass, asdict
import dhlab as dh
import pandas as pd
from flask_cors import cross_origin
import dhlab.text.conc_coll as conc_coll
import jinja_partials
from typing import Counter, Self
from dhlab.api.dhlab_api import totals
import dhlab.nbtext as nb
from wordcloud import WordCloud
#import wordcloud
import matplotlib.pyplot as plt
import io
import base64

def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = "superhemmelig-noekkel"  # Required for session management
    
    @app.route("/")
    def index() -> str:
        return render_template(
            "index_base.html",
            app_title="Korpus | Konkordanser | Kollokasjoner",
            app_name="Korpus | Konkordanser | Kollokasjoner",
        )
    
    @app.route("/corpus-method", methods=['GET', 'POST'])
    def corpus_method() -> str:
        type_ = request.args.get("type_")
        if type_ == "build_corpus":
            return render_template("corpus_builder.html")
        elif type_ == "upload_corpus":
            return render_template("corpus_uploader.html")
        else:
            raise ValueError(f"Unknown corpus method: {type_}")

    @app.route("/submit-form", methods=['GET', 'POST'])
    def make_corpus() -> str:
        if request.files:
            uploaded_file = request.files['spreadsheet']
            corpus = speadsheet_to_corpus(request.files)

            session['urn_list'] = corpus.frame['urn'].tolist()
            json_table = corpus.frame.to_json(orient="records")
        else:
            corpus_metadata = CorpusMetadata.from_dict(request.form)
            
            session['corpus_metadata'] = asdict(corpus_metadata)
            
            corpus = create_corpus(corpus_metadata)
            json_table = corpus.frame.to_json(orient="records")
            doctype = corpus["doctype"].iloc[0]
            selected_columns = process_corpus_data(corpus, doctype)

        return render_template(
            "table.html",
            json_table=json_table,
            res_table=selected_columns.to_html(table_id="results_table", border=0),
        )

    @app.route("/search-form-action")
    def choose_action() -> str:
        type_ = request.args.get("type_")
        if type_ == "search-collocation":
            return render_template("search-collocation.html")
        if type_ == "search-concordance":
            return render_template("search-concordance.html")
        else:
            raise ValueError(f"Unknown action: {type_}")
    
    @app.route("/search_concordance")
    @cross_origin()
    def search_concordances() -> str:
        # Retrieve corpus metadata from session
        if 'urn_list' in session:
            corpus = dh.Corpus()
            corpus.extend_from_identifiers(session['urn_list'])
        elif 'corpus_metadata' in session:
            corpus_metadata = CorpusMetadata(**session['corpus_metadata'])
            corpus = create_corpus(corpus_metadata)
        else:
            raise ValueError("No corpus data found in session")

        query = request.args.get("search")
        window = int(request.args.get("window", 20))
        concordances = conc_coll.Concordance(corpus, query, limit=10, window=window)

        resultframe = process_concordance_results(concordances, corpus)
        
        return jinja_partials.render_partial(
            "concordance_results.html",
            resultframe=resultframe
        )
    
    @app.route("/search_collocation")
    @cross_origin()
    def search_collocations() -> str:
        """ 
        1) Bygg kollokasjonen

        2) Finn en referanse

        3) Sammenlign kollokasjon med referanse
        """
        if 'urn_list' in session:
            corpus = dh.Corpus()
            corpus.extend_from_identifiers(session['urn_list'])
        elif 'corpus_metadata' in session:
            corpus_metadata = CorpusMetadata(**session['corpus_metadata'])
            corpus = create_corpus(corpus_metadata)
        else:
            raise ValueError("No corpus data found in session")
        
        words = request.args.get("search")
        print(type(words))
        #reference_corpus = request.args.get("ref_korpus")
        words_before = request.args.get("words_before", 10)
        print(type(words_before))
        words_after = request.args.get("words_after", 10)

        #Bygg kollokasjon
        tot = totals(50000) #referansekorpus- skal erstattes med csv-er senere
        coll = corpus.coll(words=words, before=int(words_before), after=int(words_after), samplesize=1000, reference=tot)
        
        coll_sorted = coll.frame.sort_values(ascending=False, by="relevance")
        #coll_sorted.columns = ['Kollokat'] + coll_sorted.columns[0:].tolist()
        #print(coll_sorted.head(5))
        resultframe = coll_sorted

        #wc = make_wordcloud(coll_sorted)
        
        return render_template(
            "collocation_results.html",
            resultframe=resultframe
            #coll_sorted=coll_sorted.to_html(table_id="coll_table", border=0), 
            #wordcloud=wordcloud
        )

    return app

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
        corpus.frame, 
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

def make_wordcloud(df, word_column="Kollokat", relevance_column='relevance', 
                      width=800, height=400, background_color='white'):
    # Create dictionary where word frequencies are based on relevance scores
    word_freq = dict(zip(df[word_column], df[relevance_column]))
    
    wc = WordCloud(width=800, height=400).generate_from_frequencies(word_freq)
    return wc

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


def speadsheet_to_corpus(file) -> dh.Corpus:
    uploaded_file = file.get('spreadsheet')
    
    if uploaded_file.filename.endswith('.csv'):
        df = pd.read_csv(uploaded_file)

    elif uploaded_file.filename.endswith('.xls') or uploaded_file.filename.endswith('.xlsx'):
        df = pd.read_excel(uploaded_file)

    urn_list = df["urn"].dropna().tolist() 
    
    return urn_list_to_corpus(tuple(urn_list))


@lru_cache
def urn_list_to_corpus(urn_list: tuple[str]) -> dh.Corpus:
    corpus = dh.Corpus()
    corpus.extend_from_identifiers(list(urn_list))
    return corpus

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
    "tidlig nynorsk (før 1875)": "reference/nob_1848_1875.csv"
}


def process_corpus_data(corpus: dh.Corpus, doctype: str) -> pd.DataFrame:
    return corpus.frame[CORPUS_COLUMNS[doctype]]


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)