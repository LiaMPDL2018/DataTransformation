import json
import xmltodict

transformedFileName = "sample"
with open(transformedFileName + '.xml', 'r', encoding="utf8") as f:
    xmlString = f.read()
xmlDict = json.loads(json.dumps(xmltodict.parse(xmlString), indent = 2))# dict of xml content
with open("tempjson.json", 'r') as fj:
    jsonString = fj.read()
jsondict = json.loads(jsonString) # dict of json template

def findByValue(value, orglist):
    if type(orglist)!=list:
        orglist = [orglist]
    for org in orglist:
        if org['@id'] == value:
            return org

xmlArt = xmlDict['article']
xmlAdmin = xmlArt['art-admin']
xmlFront = xmlArt['art-front']

authors = xmlFront['authgrp']['author']
orgs = xmlFront['authgrp']['aff']
for author in authors:
    # print(author)
    aff = author['@aff']
    if len(aff)>4:
        afflist = aff.split()
        for affele in afflist:
            print("more than 1")
            org = findByValue(affele, orgs)
            print(affele)
            print(org['@id'])
    else:
        org = findByValue(aff, orgs)
        print(aff)
        print(org['@id'])

# how to load a .py file in python environment
# exec(open("./path/to/script.py").read(), globals())
