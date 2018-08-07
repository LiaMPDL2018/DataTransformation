import json
import xmltodict
import copy
import pandas as pd
from pyExcelReader import pyExlDict

def findByValue(value, orglist):
    if type(orglist)!=list:
        orglist = [orglist]
    for org in orglist:
        if org['@id'] == value:
            return org
def find(key, dictionary):
    for k, v in dictionary.items():
        if k == key:
            yield v
        elif isinstance(v, dict):
            for result in find(key, v):
                yield result
        elif isinstance(v, list):
            for d in v:
                for result in find(key, d):
                    yield result
transformedFileName = "sample"
# ==== supplement mapping files ====
fileMonthNum = '.\subsidiary_doc\Month.xlsx'
fileAbbrRSC = '.\subsidiary_doc\Abbr-RSC.xlsx'

dictMonthNum = pyExlDict(fileMonthNum)
# print(dictMonthNum)
dictAbbrJournal = pyExlDict(fileAbbrRSC)
# print(dictAbbrJournal)

# ==== dict to read from ====
with open(transformedFileName + '.xml', 'r', encoding="utf8") as f:
    xmlString = f.read()
xmlDict = json.loads(json.dumps(xmltodict.parse(xmlString), indent = 2))# dict of xml content
xmlArt = xmlDict['article']
xmlAdmin = xmlArt['art-admin']
xmlFront = xmlArt['art-front']
# ==== dict to write in ====
with open("tempjson.json", 'r') as fj:
    jsonString = fj.read()
jsondict = json.loads(jsonString) # dict of json template

# ==== transformation process ====
jsondict['context']['objectId'] = 'ctx_persistent3'

metaData = jsondict['metadata']
# ---- search for title ----
metaData['title'] = xmlFront['titlegrp']['title']['#text']

# ---- add authors ----
authors = xmlFront['authgrp']['author']
orgs = xmlFront['authgrp']['aff']
creator = metaData['creators'][0]
metaData['creators'] = []
# print(creator)
for author in authors:
    creatorTemp = creator.copy()
    creatorTemp['person']['givenName'] = author['person']['persname']['fname']
    creatorTemp['person']['familyName'] = author['person']['persname']['surname']
    aff = author['@aff'].split()
    creatorTemp['person']['organizations'] = []
    for affele in aff:
        org = findByValue(affele, orgs)
        name = org['org']['orgname']['nameelt']
        address = ', '.join(list(org['address'].values()))
        if isinstance(name, list):
            name = ', '.join(name)
        creatorTemp['person']['organizations'].append(
            {'identifier':'ou_976546', 'name':name, 
            'address':address})
    storeCreator = copy.deepcopy(creatorTemp)
    metaData['creators'].append(storeCreator)
# ---- dates ----
xmlReceived = xmlAdmin['received']
year = xmlReceived['date']['year']
month = dictMonthNum[xmlReceived['date']['month']]
day = xmlReceived['date']['day']
metaData['dateSubmitted'] = year +'-' + month + '-' + day
# print((metaData['dateSubmitted']))
xmlDate = xmlAdmin['date']
year = xmlDate['year']
month = dictMonthNum[xmlDate['month']]
day = xmlDate['day']
metaData['dateAccepted'] = year +'-' + month + '-' + day
# print(metaData['dateAccepted'])
del metaData['dateModified'] # no information can be assigned
xmlPub = xmlArt['published']
year = xmlPub[0]['pubfront']['date']['year']
month = dictMonthNum[xmlPub[0]['pubfront']['date']['month']]
day = xmlPub[0]['pubfront']['date']['day']
metaData['datePublishedOnline'] = year +'-' + month + '-' + day
# print(metaData['datePublishedOnline'])
year = xmlPub[1]['pubfront']['date']['year']
try:
    month = dictMonthNum[xmlPub[1]['pubfront']['date']['month']]
except:
    month = xmlPub[1]['pubfront']['date']['month']
day = xmlPub[1]['pubfront']['date']['day']
if (year == "Unassigned" or month == "Unassigned" or day == "Unassigned"):
    del metaData['datePublishedInPrint']
else:
    metaData['datePublishedInPrint'] = year +'-' + month + '-' + day
# print(metaData['datePublishedInPrint'])
# ---- event ----
del metaData['event'] # no infomation can be assigned
# ---- doi ----
metaData['identifiers'][0]['id'] = xmlAdmin['doi']

# ---- sources ----
source = metaData['sources'][0]
source['title'] = dictAbbrJournal[xmlPub[0]['journalref']['link']]
source['volume'] = xmlPub[1]['volumeref']['link']
source['issue'] = xmlPub[1]['issueref']['link']
source['startPage'] = xmlPub[1]['pubfront']['fpage']
source['endPage'] = xmlPub[1]['pubfront']['lpage']
# print(source)

# ---- freeKeywords ----
if isinstance(xmlArt['art-front']['art-toc-entry']['ictext'], dict):
    metaData['freeKeywords'] =  xmlArt['art-front']['art-toc-entry']['ictext']['#text']
else:
    metaData['freeKeywords'] =  xmlArt['art-front']['art-toc-entry']['ictext']

# ---- abstracts ----list
metaData['abstracts'][0]['value'] = xmlArt['art-front']['abstract']['p']['#text']
# ---- subjects ----
del metaData['subjects'] # no information can be assigned

# ---- num of pages ----
metaData['totalNumberOfPages'] = xmlPub[1]['pubfront']['no-of-pages']

# ---- projectInfo ----list
xmlLinks = xmlArt['art-links']
project = metaData['projectInfo'][0]
project['grantIdentifier']['id'] = xmlLinks['fundgrp']['funder']['award-number']
project['fundingInfo']['fundingOrganization']['title'] = xmlLinks['fundgrp']['funder']['funder-name']

# ---- files ---- list
jsondict['files'][0]['metadata']['title'] = transformedFileName + '.pdf'


jsonwrite = json.dumps(jsondict, indent=2)

# save step
with open("output.json", 'w') as f:
    f.write(jsonwrite) # output the json format of xml content
