import os
import json

from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn, requests
import unidecode
from nltk import word_tokenize
from nltk.corpus import stopwords

app = FastAPI(docs_url="/")

solr_host = os.getenv("SOLR_HOST", "host.docker.internal")
title_weight_multiplier = os.getenv("ROWS", 20)
text_weight_multiplier = os.getenv("ROWS", 2)
rows = os.getenv("ROWS", 200)

params = f"?fl=score&fl=*&defType=edismax&qf=_title_^{title_weight_multiplier}+_text_^{text_weight_multiplier}&rows={rows}"

headers = {
    'Content-Type': 'application/json'
}


request_object = {
  "query": "query_replacement",
  "facet": {
    "url" : {
      "type": "terms",
      "field": "base_url",
      "limit": 10
    },
    "size":{
      "type": "terms",
      "field": "size",
      "limit": 300
    }
  }
}


@app.get("/query")
async def query_endpoint(q:str):
    try:
        first_response = requests.post(f"http://{solr_host}:8983/solr/mycore/query{params}", headers=headers ,data=json.dumps(request_object).replace("query_replacement", q))
        first_response_json = first_response.json()
        if first_response_json['response']['numFound'] > 0:
            return {"results": [first_response_json]}
        
        fuzzy_query = get_clean_query(q)
        second_response = requests.post(f"http://{solr_host}:8983/solr/mycore/query{params}", headers=headers ,data=json.dumps(request_object).replace("query_replacement", fuzzy_query))
        second_response_json = second_response.json()
        return {"results": [second_response_json]}

    except BaseException as ex:
        return []


def get_clean_query(q):
    #lower case
    clean_query = q.lower() 
    #remove accents
    clean_query = unidecode.unidecode(clean_query) 
    #tokenize
    tokens = word_tokenize(clean_query, language="spanish")
    #Remove punctuations, other formalities of grammar
    tokens = [word for word in tokens if word.isalpha()]
    #Remove white spaces and StopWords
    tokens = [word for word in tokens if not word in stopwords.words("spanish")]
    
    clean_query = ""
    for token in tokens:
        word = str(token)
        if word != 'not' and word != 'and' and word != 'or':
            clean_query = clean_query + word + '~ '
        else:
            clean_query = clean_query + word + ' '

    if len(tokens) == 0:
        clean_query = '*:*'
    return clean_query


if __name__=="__main__":
    uvicorn.run("main:app",host='localhost', port=8093, reload=True, debug=True)