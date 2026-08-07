"""Test the auth fixes."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from fastapi.testclient import TestClient

os.environ["ENVIRONMENT"] = "production"
os.environ["DEBUG"] = "false"
os.environ["OWNER_EMAIL"] = "redr28126@gmail.com"

from app.main import app

client = TestClient(app)

print("=== Testing OAuth endpoints (should NOT be 403) ===\n")

resp = client.post("/api/auth/oauth/google")
print(f"POST /api/auth/oauth/google => {resp.status_code}")
assert resp.status_code != 403, "FAIL: Still 403 on OAuth!"

if resp.status_code == 200:
    data = resp.json()
    assert "oauth_url" in data
    print("PASS: OAuth endpoint returned 200 with oauth_url")
elif resp.status_code == 500:
    print("PASS: CSRF passed (500 = OAuth not configured on server)")
else:
    print(f"Unexpected: {resp.status_code}")

print("\n=== Testing CSRF still enforced on regular POST ===\n")
resp2 = client.post("/api/auth/login", json={"email": "test@test.com", "password": "short"})
print(f"POST /api/auth/login no CSRF => {resp2.status_code}")
assert resp2.status_code == 403, "FAIL: CSRF not enforced on regular login!"
print("PASS: CSRF still enforced on regular endpoints")

print("\nALL TESTS PASSED!")