import json
import requests
from io import StringIO

URL = 'https://robovinci.xyz'
with open('api_key.txt', 'r') as f:
    API_KEY = f.read().strip()
HEADERS = {
    'Authorization': f'Bearer {API_KEY}'
}

def get_best_results():
    req_url = URL + '/api/results/user'
    r = requests.get(req_url, headers=HEADERS, timeout=1)
    r.raise_for_status()
    return r.json()['results']

def submit_stream(stream, *, num):
    req_url = URL + f'/api/submissions/{num}/create'
    files = {'file': ('submission.isl', stream)}
    r = requests.post(req_url, headers=HEADERS, files=files, timeout=2)
    r.raise_for_status()
    return r.json()

def submit_str(s, *, num):
    return submit_stream(StringIO(s), num=num)

def submit_file(fname, *, num):
    return submit_stream(open(fname, 'rb'), num=num)
    

if __name__ == '__main__':
    for sub in get_best_results():
        print(f'{sub["problem_id"]} ({sub["problem_name"]}): {sub["min_cost"]}')
