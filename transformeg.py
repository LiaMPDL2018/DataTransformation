import json
import xmltodict
 
with open("sample.xml", 'r', encoding="utf8") as f:
    xmlString = f.read()

xmltemp = json.loads(json.dumps(xmltodict.parse(xmlString), indent = 4)) # dict of xml content

with open("output.json", 'w') as f:
    f.write(xmltemp) # output the json format of xml content

with open("tempjson.json", 'r') as fj:
    jsonString = fj.read()
jsontemp = json.loads(jsonString) # dict of json template
print(jsontemp)