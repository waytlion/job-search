import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("NVIDIA_API_KEY")

headers = {
    "Authorization": f"Bearer {api_key}"
}
url = "https://integrate.api.nvidia.com/v1/models"
r = requests.get(url, headers=headers)
print("STATUS CODE:", r.status_code)
if r.status_code == 200:
    models = [m['id'] for m in r.json().get('data', [])]
    print("Found", len(models), "models.")
    print("Sample:", models[:10])
else:
    print(r.text)
