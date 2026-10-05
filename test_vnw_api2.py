import requests
import json

url = "https://www.vietnamworks.com/truong-phong-kinh-doanh-sale-manager-it-product-1688622-jv"
# The API usually takes the job ID. Job ID is 1688622.
job_id = 1688622

headers = {
    'User-Agent': 'Mozilla/5.0',
    'Content-Type': 'application/json'
}
try:
    # Let's try the ms api
    r = requests.get(f'https://ms.vietnamworks.com/job-search/v1/api/job/detail?jobId={job_id}', headers=headers)
    print("GET Status:", r.status_code)
    if r.status_code == 200:
        data = r.json()
        print(data.keys())
        if 'data' in data:
            print("JD length:", len(data['data'].get('jobDescription', '')))
except Exception as e:
    print(e)
