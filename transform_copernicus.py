# automatic transformation for publications from copernicus
import json
import xmltodict
import copy
from urlRequest import loginRequest, affRequest, upfileRequest, itemsRequest
from pyExcelReader import from_DOI
# from pandas.io.json import json_normalize
# def flatten(dd, level_mark='0', prefix=''):
#     return { k if prefix else k : v
#              for kk, vv in dd.items()
#              for k, v in flatten(vv, separator, kk).items()
#              } if isinstance(dd, dict) else { prefix : dd }
def flatten_dict(d, level_mark = -1):
    level_mark += 1
    def items():
        for key, value in d.items():
            if isinstance(value, dict) and level_mark<6: # level_mark < 6 controls how deep the dict should be flatterned. If 'creators' only have one object, there will be problem if flattening down to the floor layer, so we stop at the creator layer. 
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

# def flatten_dict_or_list(d):
#     """
#     flatten a mixed dict and list nest into a dict
#     """
#     def items():
#         for key, value in d.items():
#             if isinstance(value, dict):
#                 for subkey, subvalue in flatten_dict(value).items():
#                     yield '.'.join([key,subkey]), subvalue
#             elif isinstance(value, list):
#                 list_mark = -1
#                 for each in value:
#                     list_mark += 1
#                     if isinstance(each, dict):
#                         for subkey, subvalue in flatten_dict(each).items():
#                             yield '.'.join([key,subkey])+str(list_mark), subvalue
#                     else:
#                         yield key+str(list_mark), value
#             else:
#                 yield key, value

#     return dict(items())
def post_processor(path, key, value):
    # print('path:%s \n key:%s\n value:%s\n' % (path, key, value))
    # input('enter to continue')
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
    return the value of the key that contatins keypart from the target_dict
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
    Return the affaliation dict whose attribute id = value.
    orglist is a list of all affaliation dicts.
    """
    if type(orglist)!=list:
        orglist = [orglist]
    # print(orglist)
    for org in orglist:
        if value in org['xsi:type']:
            return org

# ==== subsidiary mapping files ====
fileDOIaff = ".//copernicus//copernicus_DOI_aff.csv"

# ==== dict to read from ====
with open("./copernicus//cpd-11-2483-2015.xml", 'r', encoding="utf8") as f:#copernicus//cpd-11-2483-2015.xml
# with open("sample.xml", 'r', encoding="utf8") as f:
    xmlString = f.read()
xmldict = json.loads(json.dumps(xmltodict.parse(xmlString, postprocessor=post_processor), indent = 2))# dict of xml content
flat_dict = flatten_dict(xmldict)
# print(flat_dict)
# keys = list(flat_dict.keys())
# print("keys of xml: %s" % keys)

# ==== dict to write in ====
with open("tempjson.json", 'r') as fj:
    jsonString = fj.read()
jsondict = json.loads(jsonString) # dict of json template

# ==== transformation process ====
jsondict['context']['objectId'] = 'ctx_persistent3'
metaData = jsondict['metadata']
# ---- search for title ----
content = search_by_key('title', flat_dict)
metaData['title'] = content
print('title: %s' % content)
# ---- identifiers ----
# print(flat_dict)
content = search_by_key('identifier', flat_dict)
# print('identifiers: %s' % content)
# the structure of 'identifier' from xmldict is [{'type':'ISSN', 'text':'xxxx'},{'type':'ISBN', 'text':'xxxx'}, {'type':'DOI', 'text':'xxxx'}]
ISSN = findByValue('ISSN', content)['text']
ISBN = findByValue('ISBN', content)['text']
DOI = findByValue('DOI', content)['text'] # the key 'text' is found by looking up to the xmldict
print("IDs: %s" % DOI)
metaData['identifiers'][0]['id'] = DOI
ctxID, ouID = from_DOI(fileDOIaff, DOI)
# print("ctxID: %s \n ouID: %s" % (ctxID, ouID))
if ctxID is not 'xxx':
    jsondict['context']['objectId'] = ctxID
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
    try:
        each_flat = flatten_dict(each)
    except AttributeError:
        break
    # print(each_flat)
    # -- find the given name of the creator --
    subcon = search_by_key('given', each_flat) 
    creatorTemp['person']['givenName'] = subcon
    # --  --
    # -- find the family name of the creator --
    subcon = search_by_key('family', each_flat)
    creatorTemp['person']['familyName'] = subcon
    # --  --
    # -- find the affaliations of the creator --
    subcon = search_by_key('org', each_flat)
    # print('organizations: %s' % subcon)
    if isinstance(subcon, list): # the case that there are multiple organizations of this creator
        creatorTemp['person']['organizations'] = []
        for org in subcon:
            name = search_by_key('title', org)
            # print('each affa name: %s' % name)
            addr = search_by_key('addr', org)
            ouId = ouID # ouId = affRequest(name, ouID) # not avaliable until 26.09.2018, function needs modification after then
            creatorTemp['person']['organizations'].append({'identifier': ouId, 'name': name, 'address':addr})
    else: # the case that there is only one organization of this creator
        creatorTemp['person']['organizations'] = []
        name = subcon
        addr = search_by_key('addr', each_flat)
        ouId = ouID # ouId = affRequest(name, ouID) # not avaliable until 26.09.2018, function needs modification after then
        creatorTemp['person']['organizations'].append({'identifier': ouId, 'name': name, 'address':addr})
    metaData['creators'].append(copy.deepcopy(creatorTemp))
    # --  --
# ---- dates ----
keypart_xml = ['created', 'modified', 'online','print','issued']# # of keys here equals to the # of keys in key_json, and the order should be mapped to each other
key_json = ['dateSubmitted', 'dateModified', 'datePublishedOnline','datePublishedInPrint', 'dateAccepted']
for i in range(len(key_json)):
    content = search_by_key(keypart_xml[i], flat_dict)
    if  content == False:
        del metaData[key_json[i]]
    else:
        metaData[key_json[i]] = content
    # print(content)

# ---- events ----
content = search_by_key('event', flat_dict)
if content == False:
    del metaData['event']
else:
    print(content)
    input("enter a number and press enter to continue")

# ---- sources ----
keypart_xml = ['source', 'volume', 'issue','start','end','sequence']# # of keys here equals to the # of keys in key_json, and the order should be mapped to each other
key_json = ['title', 'volume', 'issue','startPage', 'endPage', 'sequenceNumber']
for i in range(len(key_json)):
    content = search_by_key(keypart_xml[i], flat_dict)
    if  content == False:
        del metaData['sources'][0][key_json[i]]
    else:
        metaData['sources'][0][key_json[i]] = content
# the following publisher and identifier is not at the same level as the keys in key_json, so they need to be process independently
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
    print('projectInfo:%s' % content)
    input("type in a number and press enter to continue")
    metaData['projectInfo'][0] = content

jsonwrite = json.dumps(jsondict, indent=2)
outfile = 'output.json'
with open(outfile, 'w') as f:
    f.write(jsonwrite) # output the json format of xml content