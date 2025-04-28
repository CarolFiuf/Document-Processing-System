import requests

url = "http://127.0.0.1:8000/detect"
image_path = "/Users/trung/Downloads/sample_repo/test.png"

with open(image_path, "rb") as f:
    files = {"file": f}
    response = requests.post(url, files=files)
    
print(response.json())