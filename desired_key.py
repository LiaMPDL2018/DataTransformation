import json
import xmltodict
# ==== dict to read from ====
with open("./copernicus//acp-15-3125-2015.xml", 'r', encoding="utf8") as f:
    xmlString = f.read()
xmldict = json.loads(json.dumps(xmltodict.parse(xmlString), indent = 2))# dict of xml content
# ==== dict to write in ====
with open("tempjson.json", 'r') as fj:
    jsonString = fj.read()
jsondict = json.loads(jsonString) # dict of json template
