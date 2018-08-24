import json
import xmltodict
import copy
import requests
from urlRequest import loginRequest, affRequest, upfileRequest, itemsRequest
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
            if isinstance(value, dict):
                for subkey, subvalue in flatten_dict(value, level_mark).items():
                    yield subkey+str(level_mark), subvalue
            else:
                yield key, value

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
    value = target_dict[key]
    del target_dict[key]
    return value
# ==== dict to read from ====
with open("./copernicus//acp-15-3125-2015.xml", 'r', encoding="utf8") as f:
# with open("sample.xml", 'r', encoding="utf8") as f:
    xmlString = f.read()
xmldict = json.loads(json.dumps(xmltodict.parse(xmlString, xml_attribs=False, postprocessor=post_processor), indent = 2))# dict of xml content
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

# ---- add creators ----
content = search_by_key('creator', flat_dict)
# print('creator: %s' % content)
creator = metaData['creators'][0]

if not isinstance(content, list):
    content = [content]

metaData['creators'] = []
for each in content:
    creatorTemp = creator.copy()
    each_flat = flatten_dict(each)
    # print(each_flat)
    subcon = search_by_key('given', each_flat)
    # print('givenName: %s' % subcon)
    creatorTemp['person']['givenName'] = subcon

    subcon = search_by_key('family', each_flat)
    # print('familyName: %s' % subcon)
    creatorTemp['person']['familyName'] = subcon
    try:
        subcon = search_by_key('org', each_flat)
        creatorTemp['person']['organizations'] = []
        for org in subcon:
            name = search_by_key('title', org)
            addr = search_by_key('addr', org)
            ouId = affRequest(name)
            creatorTemp['person']['organizations'].append({'identifier': ouId, 'name': name, 'address':addr})
        print('==== organizations')
    except:
        creatorTemp['person']['organizations'] = []
        name = search_by_key('title', each_flat)
        addr = search_by_key('address', each_flat)
        ouId = affRequest(name)
        creatorTemp['person']['organizations'].append({'identifier': ouId, 'name': name, 'address':addr})
    # print(each_flat)
    metaData['creators'].append(copy.deepcopy(creatorTemp))
    
# ---- dates ----
