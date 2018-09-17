# automatic transformation for publications from RSC
import json # packadge used for json files
import xmltodict # packadge used for xml files
import copy # packadge to copy nested dict variables
import os
from pyExcelReader import pyExlDict, from_DOI # functions reading from .xlsx or .csv files
from urlRequest import loginRequest, affRequest, upfileRequest, itemsRequest # functions to interact with PuRe via REST API
# ==== help function for transformation ====
def findByValue(value, orglist):
    """
    Return the affaliation dict whose attribute id = value.
    orglist is a list of all affaliation dicts.
    """
    if type(orglist)!=list:
        orglist = [orglist]
    for org in orglist:
        if org['@id'] == value:
            return org
def xmlNamesPaths(desiredPath):
    """
    Return the iterative list of file names, filepaths and folder paths in the desiredPath folder
    """
    for root, _, filenames in os.walk(desiredPath):
        for f in filenames:
            if f.endswith('.xml'):
                filepath = os.path.join(root, f)
                yield os.path.splitext(f)[0], filepath, root
def flatten(lst):
    """
    Put a nested list into a flat list
    """
    new_lst = []
    flatten_helper(lst, new_lst)
    return new_lst

def flatten_helper(lst, new_lst):
	for element in lst:
		if isinstance(element, list):
			flatten_helper(element, new_lst)
		else:
			new_lst.append(element)
# ==== supplement mapping files ====
fileMonthNum = './/subsidiary_doc//Month.xlsx'
fileAbbrRSC = './/subsidiary_doc//Abbr-RSC.xlsx'
fileDOIaff = './/30759//rsc_201701-201807.csv'
dictMonthNum = pyExlDict(fileMonthNum)
dictAbbrJournal = pyExlDict(fileAbbrRSC)

desiredPath = './30759'

# ==== query: log in - get token ====
namePass = "hlia:hard2Remember"
Token = loginRequest(namePass)

# ==== process iteratively for all the .xml in the folders and subforders
for name, filePath, folderPath in xmlNamesPaths(desiredPath):
    print(name, filePath)                
    transformedFileName = name

    # ==== load xml metadata dict to read from ====
    with open(filePath, 'r', encoding="utf8") as f:
        xmlString = f.read()
    xmlDict = json.loads(json.dumps(xmltodict.parse(xmlString), indent = 2))# dict of xml content
    xmlArt = xmlDict['article']
    xmlAdmin = xmlArt['art-admin']
    xmlFront = xmlArt['art-front']
    # ==== load json metadata template dict to write in ====
    with open("tempjson.json", 'r') as fj:
        jsonString = fj.read()
    jsondict = json.loads(jsonString) # dict of json template

    # ==== transformation process ====
    metaData = jsondict['metadata']
    # ---- search for title ----
    if isinstance(xmlFront['titlegrp']['title'], dict):
        metaData['title'] = xmlFront['titlegrp']['title']['#text']
    else:
        metaData['title'] = xmlFront['titlegrp']['title']
    # ---- doi ----
    metaData['identifiers'][0]['id'] = xmlAdmin['doi']
    ctxID, ouID = from_DOI(fileDOIaff, xmlAdmin['doi'])
    """
    ctx id of the one who will receive this publication item: 
    ctx_persistent3 is Lia for testing purpose
    ctxID is the one to whom the item should be sent to
    change 'ctx_persistent3' to ctxID in the following line when doing real data transformation and uploading
    """
    jsondict['context']['objectId'] = 'ctx_persistent3' #ctxID 

    # ---- add authors ----
    authors = xmlFront['authgrp']['author']
    orgs = xmlFront['authgrp']['aff']
    creator = metaData['creators'][0]
    metaData['creators'] = []
    for author in authors:
        creatorTemp = creator.copy()
        creatorTemp['person']['givenName'] = author['person']['persname']['fname']
        if isinstance(author['person']['persname']['surname'], dict):
            creatorTemp['person']['familyName'] = author['person']['persname']['surname']['#text']
        else:
            creatorTemp['person']['familyName'] = author['person']['persname']['surname']
        aff = author['@aff'].split()
        creatorTemp['person']['organizations'] = []
        for affele in aff:
            org = findByValue(affele, orgs)
            name = org['org']['orgname']['nameelt']
            if isinstance(name, list):
                name = ', '.join(name)
            # print(name)
            # --== query: affiliation Id ==--
            ouId = affRequest(name, ouID)
            print(ouId)
            address = ', '.join(flatten(list(org['address'].values())))
            creatorTemp['person']['organizations'].append(
                {'identifier': ouId, 'name': name, 
                'address':address})
        storeCreator = copy.deepcopy(creatorTemp)
        metaData['creators'].append(storeCreator)
    # ---- dates ----
    # -- dateSubmitted --
    xmlReceived = xmlAdmin['received']
    year = xmlReceived['date']['year']
    month = dictMonthNum[xmlReceived['date']['month']]
    day = xmlReceived['date']['day']
    if len(day) < 2:
        day = '0' + day
    metaData['dateSubmitted'] = year +'-' + month + '-' + day
    # print((metaData['dateSubmitted']))
    # -- dateAcceptd --
    xmlDate = xmlAdmin['date']
    year = xmlDate['year']
    month = dictMonthNum[xmlDate['month']]
    day = xmlDate['day']
    if len(day) < 2:
        day = '0' + day
    metaData['dateAccepted'] = year +'-' + month + '-' + day
    # print(metaData['dateAccepted'])
    # -- dateModiefied --
    del metaData['dateModified'] # no information can be assigned
    # -- datePublishedOnline -- 
    xmlPub = xmlArt['published']
    year = xmlPub[0]['pubfront']['date']['year']
    month = dictMonthNum[xmlPub[0]['pubfront']['date']['month']]
    day = xmlPub[0]['pubfront']['date']['day']
    if len(day) < 2:
        day = '0' + day
    metaData['datePublishedOnline'] = year +'-' + month + '-' + day
    # print(metaData['datePublishedOnline'])
    # -- datePublishedInPrint -- 
    year = xmlPub[1]['pubfront']['date']['year']
    try:
        month = dictMonthNum[xmlPub[1]['pubfront']['date']['month']]
    except:
        month = xmlPub[1]['pubfront']['date']['month']
    day = xmlPub[1]['pubfront']['date']['day']
    if len(day) < 2:
        day = '0' + day
    if (year == "Unassigned" or month == "Unassigned" or day == "Unassigned"):
        del metaData['datePublishedInPrint']
    else:
        metaData['datePublishedInPrint'] = year +'-' + month + '-' + day
    # print(metaData['datePublishedInPrint'])
    # ---- event ----
    del metaData['event'] # no infomation can be assigned
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
    if isinstance(xmlArt['art-front']['abstract']['p'], dict):
        metaData['abstracts'][0]['value'] = xmlArt['art-front']['abstract']['p']['#text']
    else:
        metaData['abstracts'][0]['value'] = xmlArt['art-front']['abstract']['p']
    # ---- subjects ----
    del metaData['subjects'] # no information can be assigned

    # ---- num of pages ----
    metaData['totalNumberOfPages'] = xmlPub[1]['pubfront']['no-of-pages']

    # ---- projectInfo ----list
    if 'art-links' in xmlArt.keys():
        xmlLinks = xmlArt['art-links']
        if 'fundgrp' in xmlLinks.keys():
            project = metaData['projectInfo'][0]
            if isinstance(xmlLinks['fundgrp']['funder'], dict):
                project['grantIdentifier']['id'] = xmlLinks['fundgrp']['funder']['award-number']
                project['fundingInfo']['fundingOrganization']['title'] = xmlLinks['fundgrp']['funder']['funder-name']
            elif isinstance(xmlLinks['fundgrp']['funder'], list):
                print("%s: multiple funders" % transformedFileName)
                metaData['projectInfo'] = []
                for funder in xmlLinks['fundgrp']['funder']:
                    projectTemp = project.copy()
                    grantId = funder['award-number']
                    if isinstance(grantId, list):
                        grantId = ','.join(grantId)
                    projectTemp['grantIdentifier']['id'] = grantId
                    projectTemp['fundingInfo']['fundingOrganization']['title'] = funder['funder-name']
                    projectStore = copy.deepcopy(projectTemp)
                    metaData['projectInfo'].append(projectStore)
            else:
                print("fungrp in %s.xml is neither dict nor list" % transformedFileName)
                pass
        else:
            print("%s: no projectInfo" % transformedFileName)
            del metaData['projectInfo']
    else:
        print("%s: no projectInfo" % transformedFileName)
        del metaData['projectInfo']
    # ---- files ---- list
    jsondict['files'][0]['metadata']['title'] = transformedFileName.upper() + '.pdf'
    # --== query: staging - uploading files ==-- 
    pdfPath = folderPath +'\\' + transformedFileName.upper() + '.pdf'
    upfileId = upfileRequest(Token, pdfPath, transformedFileName)
    if upfileId == "No PDF":
        print("item" + name + "has no PDF attached")
        del jsondict['files']
    else:
        jsondict['files'][0]['content'] = upfileId

    jsonwrite = json.dumps(jsondict, indent=2) # conver json obj to string to upload via REST API
    
    # --== query: items - publication ==--
    item_res = itemsRequest(Token, jsonwrite)
    if item_res.ok==False:
        print("item" + name + "metadata uploading fail")
    