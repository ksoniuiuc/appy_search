import json
from elastic_enterprise_search import AppSearch
from flask import Flask, render_template, request
import requests
import time

app = Flask(__name__)

with open("config.json") as json_data_file:
    config = json.load(json_data_file)

client = AppSearch(
    config['appsearch']['base_endpoint'],
    http_auth=config['appsearch']['api_key'])

engine_name = config['appsearch']['engine_name']
api_url = config['mm_api']['url']
api_key = config['mm_api']['key']
api_format = config['mm_api']['format']

@app.route("/")
def home():
    data = client.search(engine_name, body={
        "query": ""
    })
    search_type = 'artist'
    return render_template("index.html", data=data['results'], 
                            search_type=search_type)


@app.route("/search", methods=['POST'])
def search():
    query = request.form['search']
    search_type = request.form['search_type']
    print(f'query {query}')
    if query!="":
        data = client.search(engine_name, body={
            "query": query
        })
        api_response = ""
        if not data["results"] or len(data["results"]) < 20:
            api_response = read(query, search_type)
            data = client.search(engine_name, body={
                "query": query
            })
            api_response = "Data Found" if api_response else ""
    else:
        data = None
        api_response = 'Please Enter text in the Search Bar...'
    return render_template("index.html", data=data, 
            api_response=api_response if api_response else "No Data Found",
            search_type=search_type)


@app.route("/index")
def index():
    # Opening JSON file
    f = open('data.json', )

    # returns JSON object as
    # a dictionary
    documents = json.load(f)
    data = client.list_documents(engine_name)
    #data = client.index_documents(engine_name, documents)
    data = [items['id'] for items in data['results']]
    return render_template("about.html", data=data)


@app.route("/delete")
def delete():
    # get data from the client
    data = client.list_documents(engine_name)
    #data = client.index_documents(engine_name, documents)
    doc_ids = [items['id'] for items in data['results']]
    if doc_ids:
        data = client.delete_documents(engine_name, document_ids=doc_ids)
    return render_template("index.html", data=data)


def read(query, search_type):
    matcher = "track.search"
    if search_type == 'artist':
        matcher_string = f'&q_artist={query}'
        rating_criteria = f'&s_{search_type}_rating'
        
    elif search_type == 'track':
        matcher_string = f'&q_track={query}'     
        rating_criteria = f'&s_{search_type}_rating'
    else:
        matcher_string = f'&q_lyrics={query}'   
        rating_criteria = f'&s_track_rating'
    
    api_call = api_url + matcher + api_format + matcher_string + rating_criteria + api_key
    request = requests.get(api_call)
    data = request.json()
    data = [item['track'] for item in data['message']["body"]['track_list']]
    #print(data)
    if data:
        with open('data.json', 'w') as outfile:
            json.dump(data, outfile)
        response = client.index_documents(engine_name, data)
        time.sleep(0.1)
        return response
    else:
        return []

    


if __name__ == "__main__":
    app.run(debug=False)
