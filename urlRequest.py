import requests
import json

def affRequest(name):
    for symb in "?/;:!":
        name = name.replace(symb,'')
    name_part = name.replace(',',' ').replace('-',' ').split()
    print("target name: %s" % name)
    internalFlag = False
    if "MPI" in name_part:
        # print("internal aff")
        internalFlag = True
        name = "Max Planck Institute " + name
        # name_part.append("Max-Planck-Institute")
    elif (sum(["Max" in p for p in name_part]) and sum(["Planck" in p for p in name_part]) and sum(["Institut" in p for p in name_part])):
        # print("internal aff")
        internalFlag = True
        name = "MPI " + name
    #     name_part.append("MPI")
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
            print("founded names:")
            inum = 0
            for aff in jData['records']:
                print("%s: %s" % (inum, aff['data']['name']))
                inum += 1
            right_seq = input("Enter the sequence number of matched name (press Enter if none):")
            if right_seq == '':
                if internalFlag:
                    ouId = 'ou_persistant13'
                else:
                    ouId = 'oupersistant22'
            else:
                right_num = int(right_seq)
                ouId = jData['records'][right_num]['data']['objectId']
        elif internalFlag:
            ouId = 'ou_persistant13'
        else:
            print("external affa")
            ouId = 'oupersistant22'
        # print(ouId)
        return ouId
    else:
    # If response code is not ok (200), print the resulting http error code with description
        print(json.dumps(data))
        # response.raise_for_status()
