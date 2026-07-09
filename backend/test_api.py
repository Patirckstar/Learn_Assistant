import requests

response = requests.post('http://localhost:8000/api/quiz/papers/refresh', stream=True)
response.encoding = 'utf-8'

for line in response.iter_lines():
    if line:
        print(line.decode('utf-8'))