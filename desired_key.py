import json
import xmltodict
# ==== dict to read from ====
with open("sample.xml", 'r', encoding="utf8") as f:
    xmlString = f.read()
xmldict = json.loads(json.dumps(xmltodict.parse(xmlString), indent = 2))# dict of xml content
# ==== dict to write in ====
with open("tempjson.json", 'r') as fj:
    jsonString = fj.read()
jsondict = json.loads(jsonString) # dict of json template

# ==== key check ====
keyl1 = list(xmldict.keys())

keyl2 = list(xmldict['article'].keys())
xmlArt = xmldict['article']
print(list(xmlArt.keys()))
xmlAdmin = xmlArt['art-admin']
print(list(xmlAdmin.keys()))
xmlPub = xmlArt['published']
# print(xmlPub)
xmlLinks = xmlArt['art-links']
xmlFront = xmlArt['art-front']
orgs = xmlFront['authgrp']['aff']
# def find(key, dictionary):
#     if isinstance(dictionary, dict):
#         for k, v in dictionary.items():
#             # print(k,v)
#             if k == key:
#                 yield k, v
#             elif isinstance(v, dict):
#                 for result in find(key, v):
#                     yield result
#             elif isinstance(v, list):
#                 for d in v:
#                     for result in find(key, d):
#                         yield result
#     else:
#         pass
# # example = {'app_url': '', 'models': [{'perms': {'add': True, 'change': True, 'delete': True}, 'add_url': '/admin/cms/news/add/', 'admin_url': '/admin/cms/news/', 'name': ''},{'perms': {'add': True, 'change': True, 'delete': True}, 'add_url': '/admin/cms/news/add/', 'admin_url': '/admin111/cms/news/', 'name': ''}], 'has_module_perms': True, 'name': u'CMS'}
# for item in find('date', xmldict):
#     print(item)
# # print(find())