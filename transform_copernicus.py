# automatic transformation for publications from copernicus
import json
import xmltodict
import copy
import os
from urlRequest import loginRequest, affRequest, upfileRequest, itemsRequest # functions to interact with PuRe via REST API
from pyExcelReader import from_DOI # function to read from .xlsx or .csv files

def xmlNamesPaths(desiredPath):
    """
    Return the iterative list of file names, filepaths and folder paths in the desiredPath folder
    """
    for root, _, filenames in os.walk(desiredPath):
        for f in filenames:
            if f.endswith('.xml'):
                filepath = os.path.join(root, f)
                yield os.path.splitext(f)[0], filepath, root

def flatten_dict(d, level_mark = -1):
    """
    This function converts a nested dict d into a flat dict in order to make searching a certain key easier.
    The key of previous layer is added into the key of current layer.
    level_mark is used to mark how deep the current layer is, also added into the key of current layer.
    """
    level_mark += 1
    def items():
        for key, value in d.items():
            if isinstance(value, dict) and level_mark<6: # level_mark < 6 controls how deep the dict should be flatterned. If 'creators' only have one object, there will be problem if flattening down to the deepest layer, so we stop at the creator layer. 
                if ':' in key:
                    ind = key.index(':')
                    prekey = key[ind+1:]
                else:
                    prekey = key
                for subkey, subvalue in flatten_dict(value, level_mark).items():
                    yield str(level_mark)+prekey+subkey, subvalue
            else:
                if ':' in key:
                    ind = key.index(':')
                    outkey = key[ind+1:]
                yield outkey, value

    return dict(items())

def post_processor(path, key, value):
    """
    a function called in xmltodict.parse(... , postprocessor=post_processor, ...) 
    delete the '@', '#' symbols in the keys
    """
    if '@' in key:
        for tar in ['ISSN', 'ISBN', 'DOI']:
            if tar in value:
                # print(value)
                key = key.replace('@','')
                return key, value
        pass
    elif '#' in key:
        key = key.replace('#','')
        return key, value
    else:
        return key, value
def search_key(keypart, keys):
    """
    search keys for the key that contains keypart
    output: matched key name
    """
    for key in keys:
        if keypart in key:
            return key
def search_by_key(keypart, target_dict):
    """
    return the value of the key that contatins keypart from the dict 'target_dict'
    if the keypart is founded, delete the (key,value) pair from the dict 'target_dict'
    else, return False
    output: the content
    """
    key = search_key(keypart, list(target_dict.keys()))
    try:
        value = target_dict[key]
    except KeyError:
        return False
    del target_dict[key]
    return value
def findByValue(value, orglist):
    """
    This function here is used to find the identifiers of the item.
    'value' is the identifier's type, e.g., ISSN, DOI
    'orglist' is the list of all identifiers.
    Return the dict whose attribute id = value.
    """
    if type(orglist)!=list:
        orglist = [orglist]
    for org in orglist:
        if value in org['xsi:type']: # the key 'xsi:type' is known by understanding the structure of the .xml files
            return org

# ==== subsidiary mapping files ====
fileDOIaff = ".//copernicus//copernicus_DOI_aff.csv" # the helping file providing the mapping between DOI of metadata and the ctxID of the affiliation where the item should be sent to and the ou_ID of the corresponding author.

desiredPath = './/copernicus' # where stores the metadata files that is to be transformed

# ==== query: log in - get token ====
namePass = "***REMOVED***:***REMOVED***"
Token = loginRequest(namePass)

# ==== process iteratively for all the .xml in the folders and subforders
for transformedFileName, filePath, folderPath in xmlNamesPaths(desiredPath):
    print(transformedFileName, filePath, folderPath)

    # ==== load xml metadata dict to read from ====
    # ---- dict to read from ----
    with open(filePath, 'r', encoding="utf8") as f:
        xmlString = f.read()
    xmldict = json.loads(json.dumps(xmltodict.parse(xmlString, postprocessor=post_processor), indent = 2)) # dict of xml metadata
    flat_dict = flatten_dict(xmldict)

    # ---- json template dict to write in ----
    with open("tempjson.json", 'r') as fj:
        jsonString = fj.read()
    jsondict = json.loads(jsonString) # dict of json template

    # ==== transformation process ====
    # jsondict['context']['objectId'] = 'ctx_persistent3' # mpdl internal testing ctx_ID
    metaData = jsondict['metadata']
    # ---- search for title ----
    content = search_by_key('title', flat_dict)
    metaData['title'] = content
    print('title: %s' % content)
    # ---- identifiers ----
    content = search_by_key('identifier', flat_dict)
    # the structure of 'identifier' from xmldict is [{'type':'ISSN', 'text':'xxxx'},{'type':'ISBN', 'text':'xxxx'}, {'type':'DOI', 'text':'xxxx'}]
    try: # some example doesn't have ISSN value or ISBN value
        ISSN = findByValue('ISSN', content)['text']
    except KeyError:
        ISSN = ''
    try:
        ISBN = findByValue('ISBN', content)['text']
    except KeyError:
        ISBN = ''
    DOI = findByValue('DOI', content)['text'] # the key 'text' is found by understanding the structure of xml metadata
    print("DOI: %s" % DOI)
    metaData['identifiers'][0]['id'] = DOI
    ctxID, ouID = from_DOI(fileDOIaff, DOI)
    if ctxID is not 'xxx':
        jsondict['context']['objectId'] = ctxID # uncomment this to forward the item to corresponding affiliation
        print('ctxID: %s' % ctxID)
    # ---- add creators ----
    content = search_by_key('creator', flat_dict)
    # print('creator: %s' % content)
    creator = metaData['creators'][0]
    if not isinstance(content, list):
        content = [content]
    metaData['creators'] = []
    for each in content: 
        # ---- operate on each creator ----
        creatorTemp = creator.copy() # copy the metadata template of the creator
        each_flat = flatten_dict(each)
        # -- find the given name of the creator --
        subcon = search_by_key('given', each_flat)
        creatorTemp['person']['givenName'] = subcon
        # -- -- --
        # -- find the family name of the creator --
        subcon = search_by_key('family', each_flat)
        creatorTemp['person']['familyName'] = subcon
        # -- -- --
        # -- find the affaliations of the creator --
        subcon = search_by_key('org', each_flat)
        # print('organizations: %s' % subcon)
        if isinstance(subcon, list): # the case that there are multiple organizations of this creator
            creatorTemp['person']['organizations'] = []
            for org in subcon:
                name = search_by_key('title', org)
                # print('each affa name: %s' % name)
                addr = search_by_key('addr', org)
                # --== query: affiliation Id ==--
                ouId = affRequest(name, ouID)
                creatorTemp['person']['organizations'].append({'identifier': ouId, 'name': name, 'address':addr})
        elif subcon: # the case that there is only one organization of this creator; in this case, 'subcon' is the name of the affaliation
            creatorTemp['person']['organizations'] = []
            name = subcon
            addr = search_by_key('addr', each_flat)
            # --== query: affiliation Id ==--
            ouId = affRequest(name, ouID) 
            creatorTemp['person']['organizations'].append({'identifier': ouId, 'name': name, 'address':addr})
        else: # the case that there no organization info of this authors
            del creatorTemp['person']['organizations']
        metaData['creators'].append(copy.deepcopy(creatorTemp))
        # -- -- --
    # ---- dates ----
    keypart_xml = ['created', 'modified', 'online','print','issued']# the number of keys here equals to the number of keys in 'key_json', and the order should be mapped to each other
    key_json = ['dateSubmitted', 'dateModified', 'datePublishedOnline','datePublishedInPrint', 'dateAccepted']
    for i in range(len(key_json)):
        content = search_by_key(keypart_xml[i], flat_dict)
        if  content == False:
            del metaData[key_json[i]]
        else:
            metaData[key_json[i]] = content

    # ---- events ----
    content = search_by_key('event', flat_dict)
    if content == False:
        del metaData['event']
    else:
        # since in the examples tested so far there is no instance that contains 'event' information, it is not known how to map the 'xml-event' to 'json-event'. This part needs modification if the 'event' shows up in xml metadata in the future. 
        print('event: %s' % content)
        input("enter a number and press enter to continue")

    # ---- sources ----
    keypart_xml = ['source', 'volume', 'issue','start','end','sequence']# the number of keys here equals to the number of keys in key_json, and the order should be mapped to each other
    key_json = ['title', 'volume', 'issue','startPage', 'endPage', 'sequenceNumber']
    for i in range(len(key_json)):
        content = search_by_key(keypart_xml[i], flat_dict)
        if  content == False:
            del metaData['sources'][0][key_json[i]]
        else:
            metaData['sources'][0][key_json[i]] = content
    # the following publisher and identifiers is not at the same level as the keys above in 'key_json', so they need to be process independently
    content = search_by_key('publish', flat_dict) # find the publisher
    if  content == False:
        del metaData['sources'][0]['publishingInfo']
    else:
        metaData['sources'][0]['publishingInfo']['publisher'] = content 

    metaData['sources'][0]['identifiers'] = [{'id':ISSN, 'type':'ISSN'}]
    metaData['sources'][0]['identifiers'].append({'id':ISBN, 'type':'ISBN'})
    
    # ---- abstract ----
    content = search_by_key('abstract', flat_dict)
    if content == False:
        del metaData['abstract']
    else:
        metaData['abstracts'][0]['value'] = content

    # ---- freeKeywords ----
    content = search_by_key('subject', flat_dict)
    if content == False:
        del metaData['freeKeywords']
    else:
        metaData['freeKeywords'] = content

    # ---- totalNumberOfPages ----
    content = search_by_key('total', flat_dict)
    if content == False:
        del metaData['totalNumberOfPages']
    else:
        metaData['totalNumberOfPages'] = content
    
    # ---- projectInfo ----
    content = search_by_key('project-info', flat_dict)
    if content == False:
        del metaData['projectInfo']
    else:
        # the same situation as 'event'
        print('projectInfo: %s' % content)
        input("type in a number and press enter to continue")
        # metaData['projectInfo'][0] = content
    
    # ---- files ----
    pdfName = transformedFileName + '.pdf'
    jsondict['files'][0]['metadata']['title'] = pdfName
    pdfPath = folderPath + '\\' + pdfName
    upfileId = upfileRequest(Token, pdfPath, pdfName)
    if upfileId == "No PDF":
        print("item " + transformedFileName + " has no PDF attached")
        del jsondict['files']
    else:
        jsondict['files'][0]['content'] = upfileId

    jsonwrite = json.dumps(jsondict, indent=2)

    # --== query: items - publication ==--
    itemsRequest(Token, jsonwrite)