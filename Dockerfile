FROM python:3.12
EXPOSE 5000
WORKDIR /app
COPY requirements.txt ./requirements.txt
RUN pip3 install -r requirements.txt
COPY src/dhlab_corpus_webapp/ .
CMD python app.py
