import json

filename = ".tidalcache"

def getid():
    with open(filename, 'r') as f:
        data = json.load(f)
        try:
            return data['session_id']
        except:
            return "" # oauth will take as invalid token and will re authorize

def gettoken():
    with open(filename, 'r') as f:
        data = json.load(f)
        try:
            return data['access_token']
        except:
            return ""

def save(id, token):
    a = open(filename, "w")
    a.write("{\"session_id\":\"" + id + "\",\"access_token\":\"" + token + "\"}") # because json.dump decided not to work
    a.close()

def clearcache(): # just in case
    a = open(filename, "w")
    a.write("{\"session_id\":\"\",\"access_token\":\"\"}")
    a.close()