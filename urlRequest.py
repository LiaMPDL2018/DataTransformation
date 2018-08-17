import requests
import json

def loginRequest(namePass):
    # namePass should be a string in form of "name:password"
    url = 'https://qa.inge.mpdl.mpg.de/rest/login'
    response = requests.post(url, data=namePass)
    return response.headers['Token']
    
def affRequest(name):
    for symb in "?/;:!":
        name = name.replace(symb,'')
    name = name.replace(',',' ').replace('-',' ')
    name_part = name.split()
    # print("target name: %s" % name)
    # for i in range(int(len(name_part))):
    #     name_part[i]
    internalFlag = False
    if "MPI" in name_part:
        # print("internal aff")
        internalFlag = True
        # name = name + "Max Planck Institute "
        name_part.append("Max Planck Institute")
        name_part[0] += "^2"
        name = " ".join(name_part)
    elif (sum(["Max" in p for p in name_part]) and sum(["Planck" in p for p in name_part]) and sum(["Institut" in p for p in name_part])):
        # print("internal aff")
        internalFlag = True
        # name = name + "MPI "
        name_part.append("MPI")
        name_part[0] += "^2"
        name = " ".join(name_part)
    else:
        name = " AND ".join(name_part)
    queryText = name
    # print(queryText)

    query_string = {"fields": ["metadata.name", "name", "alternativeNames", "parentAffailiations"], "query": queryText}
    data = {"query": {"query_string":query_string},"size" : "5"}
    # print(json.dumps(data))
    # -------- send url request to search for the ouId --------
    url = 'https://qa.inge.mpdl.mpg.de/rest/ous/search'
    response = requests.post(url, data=json.dumps(data), headers={"Content-Type": "application/json"})
    if response.ok:
        jData = (response.json())
        if 'records' in jData.keys():
            # print("founded names:")
            # inum = 0
            # for aff in jData['records']:
            #     print("%s: %s" % (inum, aff['data']['name']))
            #     inum += 1
            # right_seq = input("Enter the sequence number of matched name (press Enter if none):")
            # if right_seq == '':
            #     if internalFlag:
            #         ouId = 'ou_persistant13'
            #     else:
            #         ouId = 'oupersistant22'
            # else:
            #     right_num = int(right_seq)
            #     ouId = jData['records'][right_num]['data']['objectId']
            ouId = jData['records'][0]['data']['objectId']
            # print(jData['records'][0]['data']['name'])
        elif internalFlag:
            ouId = 'ou_persistent13'
        else:
            # print("external affa")
            ouId = 'ou_persistent22'
        # print(ouId)
        return ouId
    else:
    # If response code is not ok (200), print the bad request
        print(json.dumps(data))
        # response.raise_for_status()

def upfileRequest(Token, filePath, filename):
    # Token: Authorization Token got in the login process
    # filename: the name without extension of the file wanted to upload
    url = 'https://qa.inge.mpdl.mpg.de/rest/staging/' + filename.upper() + '.pdf'
    headers = {'Authorization' : Token}
    files = {'file': open(filePath, 'rb')}
    res = requests.post(url, files = files, headers = headers)
    return res.text

def itemsRequest(Token, jsonfile):
    url = 'https://qa.inge.mpdl.mpg.de/rest/items'
    headers = {'Authorization' : Token, 'Content-Type' : 'application/json'}
    # method 1: jsonfile is json obj string, which is the body content
    res = requests.post(url, data = jsonfile, headers = headers)
    # # method 2 : jsonfile is the path+name of the json data, need to read and then become the body content 
    # with open(jsonfile, 'r') as fj:
    #     jsonString = fj.read()
    # res = requests.post(url, data = jsonString, headers = headers)
    if res.ok:
        input('press Enter to continue')
    else:
        print(res.text)
        input('press Enter to continue')