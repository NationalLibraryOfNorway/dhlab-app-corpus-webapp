# DHLab-korpus

Dette korpuset er generert med Nasjonalbibliotekets [DH-Lab](https://www.nb.no/dh-lab/) sin korpusbygger og kan brukes med [appene til DH-Laben](https://www.nb.no/dh-lab/apper/).

VIKTIG: Korpusappen tar et tilfeldig utvalg av samlingen når man bygger korpus.
Det er derfor ikke garantert at du får samme korpus når du bruker korpusbyggeren flere ganger, selv om du har samme innstillinger i korpusdefinisjonen.
Du bør passe godt på korpusfilen for reproduserbare resultater.

## Informasjon om korpuset:

Tidspunkt korpusbyggeren ble brukt: {{ timestamp }}

{% if corpus_definition -%}
{% for config, value in corpus_definition.items() %}
* `{{ config }}`: `{{ value }}`
{%- endfor %}
{% else -%}
Korpuset ble i sin helhet lastet opp av brukeren
{%- endif %}
