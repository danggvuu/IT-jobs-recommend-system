import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Content-Type': 'application/json'
}
data = {
    "userId": 0,
    "query": "it",
    "hitsPerPage": 20,
    "page": 0
}
try:
    r = requests.post('https://ms.vietnamworks.com/job-search/v1/api/job-search/search', headers=headers, json=data)
    print(r.status_code)
    print(r.json().keys())
    print("Found jobs:", len(r.json()['data']))
except Exception as e:
    print("Error:", e)
