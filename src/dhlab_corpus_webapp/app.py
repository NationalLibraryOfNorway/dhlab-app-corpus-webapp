from flask import Flask, render_template, request
import dhlab as dh
import pandas as pd

def create_app() -> Flask:
    app = Flask(__name__)

    #Route for the homepage (index)
    @app.route("/")
    def index() -> str:
        return render_template("index_base.html", res_table="")

    #Route to handle form submission and generate corpus
    @app.route('/submit-form', methods=['POST'])
    def make_corpus() -> str:
        form_data = extract_form_data(request.form)

        corpus = create_corpus(form_data)

        df_from_corpus = process_corpus_data(corpus)

        return render_template('index_base.html', 
                               corpus_name_=form_data['corpus_name'], 
                               res_table=df_from_corpus.to_html(table_id='results_table', border=0))

    return app

#Helper function to extract and organize form data
def extract_form_data(form) -> dict:
    return {
        'doc_type_selection': form.get('doc_type_selection'),
        'language': form.get('languages'),
        'author': form.get('author'),
        'title': form.get('title'),
        'words_or_phrases': form.get('words_or_phrases'),
        'key_words': form.get('key_words'),
        'dewey': form.get('dewey'),
        'from_year': form.get('from_year'),
        'to_year': form.get('to_year'),
        'search_type': form.get('search_type'),
        'num_docs': form.get('num_docs'),
        'corpus_name': form.get('corpus_name')
    }

#Helper function to create a corpus-object
def create_corpus(form_data: dict) -> dh.Corpus:
    return dh.Corpus(
        doctype=form_data['doc_type_selection'],
        author=form_data['author'],
        freetext=None,
        fulltext=form_data['words_or_phrases'],
        from_year=form_data['from_year'],
        to_year=form_data['to_year'],
        from_timestamp=None,
        title=form_data['title'],
        ddk=form_data['dewey'],
        subject=form_data['key_words'],
        lang=form_data['language'],
        limit=form_data['num_docs'],
        order_by=form_data['search_type'],
        allow_duplicates=False
    )

#Helper function to process the corpus data into a cleaned-up DataFrame
def process_corpus_data(corpus: dh.Corpus) -> pd.DataFrame:
    df = corpus.frame
    df = df[['dhlabid', 'urn', 'authors', 'title', 'city', 'timestamp', 'year', 'publisher', 'ddc', 'subjects', 'langs']]
    return df

app = create_app()

if __name__ == "__main__":
    app.run()
