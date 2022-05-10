import json


def getid():
    with open('cache.json', 'r') as f:
        data = json.load(f)
        return data['session_id']

def gettoken():
    with open('cache.json', 'r') as f:
        data = json.load(f)
        return data['access_token']

def save(id, token):
    a = open("cache.json", "w")
    a.write("{\"session_id\":\"" + id + "\",\"access_token\":\"" + token + "\"}")
    a.close()