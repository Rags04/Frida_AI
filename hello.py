# Print Hello
import requests

response = requests.get('https://www.google.com')
print(f"Wesite status code:{response.status_code}")
