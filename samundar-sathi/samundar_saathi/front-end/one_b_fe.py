import requests

url = "https://v1.nocodeapi.com/samundarsuraksha/fbsdk/OjCtcgqEGzplhVcp/firestore/allDocuments?collectionName=one_b"
params = {}
r = requests.get(url=url, params=params)
result = r.json()

# Extracting information from the first document
document = result[0]['_fieldsProto']
beach_name = document['name']['stringValue']
safety_score = document['safety_report']['mapValue']['fields']['safety_score']['integerValue']
safety_message = document['safety_report']['mapValue']['fields']['safety_message']['stringValue']
first_reason = document['safety_report']['mapValue']['fields']['reasons']['arrayValue']['values'][0]['stringValue']

# Printing the extracted information
print(f"Beach Name: {beach_name}")
print(f"Safety Score: {safety_score}")
print(f"Safety Message: {safety_message}")
print(f"Reason: {first_reason}")
