import json
import requests
from io import StringIO

URL = 'https://robovinci.xyz'
with open('api_key.txt', 'r') as f:
    API_KEY = f.read().strip()
HEADERS = {
    'Authorization': f'Bearer {API_KEY}'
}

def get_results():
    req_url = URL + '/api/results/user'
    r = requests.get(req_url, headers=HEADERS, timeout=1)
    r.raise_for_status()
    return r.json()['results']

def get_best_submissions():
    req_url = URL + '/api/submissions'
    r = requests.get(req_url, headers=HEADERS, timeout=1)
    r.raise_for_status()
    best_by_pid = {}
    for sub in r.json()['submissions']:
        pid = sub['problem_id']
        sid = sub['id']
        score = sub['score']
        if pid not in best_by_pid or best_by_pid[pid]['score'] > score:
            best_by_pid[pid] = sub
    return best_by_pid

def get_submission_url(sid):
    req_url = URL + f'/api/submissions/{sid}'
    r = requests.get(req_url, headers=HEADERS, timeout=1)
    r.raise_for_status()
    return r.json()['file_url']

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

def summary():
    tot_score = 0
    for sub in get_results():
        print(f'{sub["problem_id"]} ({sub["problem_name"]}): {sub["min_cost"]}')
        tot_score += sub["min_cost"]
    print(f'== Total: {tot_score} ==')

def generate_best_report(prefix):
    best_subs = get_best_submissions()
    for pid,sub in best_subs.items():
        url = get_submission_url(sub['id'])
        r = requests.get(url)
        r.raise_for_status()
        with open(prefix + f'/{pid}_code.isl', 'wb') as f:
            f.write(r.content)
        with open(prefix + f'/{pid}_summary.txt', 'w') as f:
            f.write(f"Cost: {sub['score']}\n")

if __name__ == '__main__':
    # summary()
    generate_best_report('lightning')
