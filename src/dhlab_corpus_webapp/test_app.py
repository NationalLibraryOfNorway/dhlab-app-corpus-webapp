from pathlib import Path
import dhlab.api.dhlab_api as dhlab_api
import dhlab.text.conc_coll as conc_coll
import pandas as pd
from flask import Flask, render_template, request, send_file, jsonify, url_for
import requests
import dhlab as dh
import pandas as pd
import io
from dataclasses import dataclass, asdict
import urllib.parse
import html

def create_app() -> Flask:
    app = Flask(__name__)
    @app.route("/")

    def index() -> str:
        return render_template("index_base.html", res_table="")
    
    @app.route('/submit-form', methods=['POST'])
    def make_corpus() -> str:
        doc_type_selection_ = request.form.get('doc_type_selection')
        language_ = request.form.get('languages')
        author_ = request.form.get('author')
        title_ = request.form.get('title')
        words_or_phrases_ = request.form.get('words_or_phrases')
        key_words_= request.form.get('key_words')
        dewey_ = request.form.get('dewey')
        from_year_ = request.form.get('from_year')
        to_year_ = request.form.get('to_year')
        search_type_= request.form.get('search_type')
        num_docs_=request.form.get('num_docs')
        corpus_name_= request.form.get('corpus_name')
        print('request forsm', request.form)
        print(type(language_))


        corpus=dh.Corpus(doctype=doc_type_selection_, 
                         author=author_, 
                         freetext=None, 
                         fulltext=words_or_phrases_, 
                         from_year=from_year_, 
                         to_year=to_year_,
                         from_timestamp=None, 
                         title=title_, 
                         ddk=dewey_, 
                         subject=key_words_, 
                         lang=language_, 
                         limit=num_docs_, 
                         order_by=search_type_, 
                         allow_duplicates=False)
        

        df_from_corpus = corpus.frame
        print("corrrp", df_from_corpus.columns)
        df_from_corpus = df_from_corpus[['dhlabid','urn', 'authors', 'title', 'city', 'timestamp', 'year', 'publisher', 'ddc', 'subjects', 'langs']]

        #print(df_from_corpus['langs'])

        return render_template('index_base.html', corpus_name_=corpus_name_, res_table=df_from_corpus.to_html(table_id='results_table', border=0, classes=[ ]))

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)