import requests

ENDPOINT = "http://127.0.0.1:8000/api/token"

response = requests.post(url=ENDPOINT, data={
                            "username":"sitanshu",
                            "password":"superman"
                        })

response = response.json()
print(response)
TOKEN = response.get('access_token')
print(TOKEN)
headers = {
        "Authorization": f"Bearer {TOKEN}"
    }
response = requests.get(url="http://127.0.0.1:8000/users/1", headers=headers)
print(response.json())
