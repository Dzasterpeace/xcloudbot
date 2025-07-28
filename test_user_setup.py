# test_user_setup.py
import requests

BASE_URL = "http://localhost:5000/api"

# Register user
register_data = {
    "email": "help@punthub.co.uk",
    "password": "Weasel11!",
    "role": "user"
}
r = requests.post(f"{BASE_URL}/auth/register", json=register_data)
print("Register:", r.status_code, r.json())

# Login user
login_data = {
    "email": "help@punthub.co.uk",
    "password": "Weasel11!"
}
r = requests.post(f"{BASE_URL}/auth/login", json=login_data)
print("Login:", r.status_code, r.json())
token = r.json().get("token")
headers = {"Authorization": f"Bearer {token}"}

# OPTIONAL: Connect Betfair manually via browser:
print("Visit /api/betfair/connect-betfair in browser to authorize Betfair")
