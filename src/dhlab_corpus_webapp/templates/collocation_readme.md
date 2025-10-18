# DHLab-kollokasjoner

Kollokasjonene er bestemt av følgende parametre:

* Basisord: {{ form.get("search") }}
* Ord før basisord: {{ form.get("words_before")}}
* Ord etter basisord: {{ form.get("words_after")}}
* Referansekorpus: {{ form.get("ref_korpus")}}
* Terskelverdi relevans: {{ form.get("relevance")}}
* Terskelverdi råfrekvens: {{ form.get("raw_freq")}}
* Maks antall kollokasjoner: {{ form.get("max_coll")}}
* Sorter etter: {{ form.get("sorting_method")}}
