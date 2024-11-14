from functools import lru_cache
from pathlib import Path
import dhlab.api.dhlab_api as dhlab_api
import dhlab.text.conc_coll as conc_coll
import httpx
import jinja_partials
import pandas as pd
from flask import Flask, render_template, request, send_file, jsonify, url_for
import requests
from flask_cors import cross_origin
from pydantic_settings import BaseSettings
import dhlab as dh
import pandas as pd
import io

##########################################
def create_app() -> Flask:
    app = Flask(__name__)
    @app.route("/")

    def index() -> str:
        return render_template("index_base.html")
    
    @app.route('/submit-form', methods=['POST'])
    def make_corpus() -> str:
        doc_type_selection_ = request.form.get('doc_type_selection')
        language_ = request.form.get('language')
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
        


        # Select the relevant columns from the dataframe
        corpus_selected = corpus[['dhlabid', 'authors', 'title', 'city', 'timestamp', 'year', 'publisher', 'ddc', 'subjects', 'langs']]
        df_from_corpus = corpus_selected.frame
        #df_from_corpus.insert(0, ' ', range(1, len(df_from_corpus) + 1))
        
        data = df_from_corpus.to_dict('records')
        print(jsonify(data))
        return jsonify(data)
        
    #@app.route('/get-results', methods=['GET'])
    #def display_search_results():
    #    dict = make_corpus()
        #Eventuelt en funksjon som retunerer søkeresultatet til websiden som en html-streng
    #    return dict
    
    @app.route('/download-excel', methods=['GET'])
    def write_to_excel():

        # Get the corpus data
        corpus_response = make_corpus()
        corpus_data = corpus_response.get_json()  # Convert JSON response to a list of dicts
        
        df = pd.DataFrame(corpus_data)
        
        # Create an in-memory Excel file
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        
        # Set the buffer position to the beginning
        output.seek(0)
        print('yoyoyoy')
    
        # Send the file as a response
        return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name='output.xlsx')

    return app

app = create_app()

if __name__ == "__main__":
    app.run()