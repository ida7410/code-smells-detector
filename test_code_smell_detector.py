import requests
import json

# Your existing API endpoint
url = "https://4fl5hk5s98.execute-api.ca-central-1.amazonaws.com/predict"

# Test code
test_code = """
def bad_function():
    if x > 0:
        if y > 0:
            if z > 0:
                if a > 0:
                    return True
"""

# Call the API
response = requests.post(
    url,
    json={"code": test_code}
)

print(json.dumps(response.json(), indent=2))