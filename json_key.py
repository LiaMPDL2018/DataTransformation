import json
import xmltodict

with open("tempjson.json", 'r') as fj:
    jsonString = fj.read()
jsondict = json.loads(jsonString) # dict of json template

# ==== key check ====
keyl1 = list(jsondict.keys())
print(keyl1)
keyl2 = list(jsondict['metadata'].keys())
print(keyl2)
source = jsondict['metadata']['sources']
project = jsondict['metadata']['projectInfo']
