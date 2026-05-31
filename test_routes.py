import sys; sys.path.insert(0, 'backend')
from fastapi.testclient import TestClient
from backend.main import app
client = TestClient(app)

# Test the generate-outline endpoint
print("=== Testing POST /api/v1/curriculum/materials/1/generate-outline ===")
resp1 = client.post('/api/v1/curriculum/materials/1/generate-outline', json={})
print(f"POST with json={{}}: {resp1.status_code} body={resp1.text[:200]}")

resp2 = client.post('/api/v1/curriculum/materials/1/generate-outline')
print(f"POST no body: {resp2.status_code} body={resp2.text[:200]}")

resp3 = client.post('/api/v1/curriculum/materials/1/generate-outline', data='')
print(f"POST data='': {resp3.status_code} body={resp3.text[:200]}")

resp4 = client.get('/api/v1/curriculum/materials/1/generate-outline')
print(f"GET: {resp4.status_code} body={resp4.text[:200]}")

print("\n=== Testing URL variations ===")
resp5 = client.post('/curriculum/materials/1/generate-outline')
print(f"POST /curriculum/... (no api/v1): {resp5.status_code} body={resp5.text[:200]}")

resp6 = client.post('/api/v1/curriculum/materials/1/generate-outline/', json={})
print(f"POST with trailing slash: {resp6.status_code} body={resp6.text[:200]}")
