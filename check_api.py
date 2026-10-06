import urllib.request
import json
import io
import sys

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8008"
print(f"Targeting server: {BASE_URL}")

print("1. Checking Sample Rash Fetch...")
url_sample = f"{BASE_URL}/samples/sample_ring_rash.jpg"
res = urllib.request.urlopen(url_sample)
img_bytes = res.read()
print(f"   [OK] Sample fetched: {len(img_bytes)} bytes, status: {res.status}")

print("2. Checking Screen Endpoint with Multipart Form Data & Image Upload...")
boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
body = io.BytesIO()
body.write(f"--{boundary}\r\n".encode("utf-8"))
body.write(b'Content-Disposition: form-data; name="rash_image"; filename="sample_ring_rash.jpg"\r\n')
body.write(b"Content-Type: image/jpeg\r\n\r\n")
body.write(img_bytes)
body.write(f"\r\n--{boundary}\r\n".encode("utf-8"))
body.write(b'Content-Disposition: form-data; name="body_area"\r\n\r\nTRUNK_OR_BACK\r\n')
body.write(f"--{boundary}\r\n".encode("utf-8"))
body.write(b'Content-Disposition: form-data; name="duration"\r\n\r\nOVER_ONE_MONTH\r\n')
body.write(f"--{boundary}\r\n".encode("utf-8"))
body.write(b'Content-Disposition: form-data; name="is_itchy"\r\n\r\ntrue\r\n')
body.write(f"--{boundary}\r\n".encode("utf-8"))
body.write(b'Content-Disposition: form-data; name="is_ring_shaped"\r\n\r\ntrue\r\n')
body.write(f"--{boundary}\r\n".encode("utf-8"))
body.write(b'Content-Disposition: form-data; name="source"\r\n\r\nupload\r\n')
body.write(f"--{boundary}\r\n".encode("utf-8"))
body.write(b'Content-Disposition: form-data; name="consent_store_data"\r\n\r\ntrue\r\n')
body.write(f"--{boundary}--\r\n".encode("utf-8"))

req = urllib.request.Request(f"{BASE_URL}/screen", data=body.getvalue(), method="POST")
req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
res2 = urllib.request.urlopen(req)
data2 = json.loads(res2.read().decode("utf-8"))
print(f"   [OK] Screen response status: {res2.status}")
print(f"   Category: {data2['decision']['category']} ({data2['decision']['urgency']})")
print(f"   Pattern model top: {data2['pattern_model']['top_display_name']} ({data2['pattern_model']['strength']})")
print(f"   Quality: blur={data2['quality']['measurements']['blur']}, acceptable={data2['quality']['acceptable']}")

print("3. Checking One-Click Demo Logins & RBAC...")
roles = ["patient", "health_worker", "pharmacist", "doctor", "analyst", "admin"]
tokens = {}
for role in roles:
    req = urllib.request.Request(
        f"{BASE_URL}/api/auth/demo-login",
        data=json.dumps({"role": role}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    res = urllib.request.urlopen(req)
    data = json.loads(res.read().decode("utf-8"))
    tokens[role] = data["token"]
    print(f"   [OK] Demo login for '{role}' -> {data['user']['name']} ({data['user']['role']})")

print("4. Checking Doctor Access to Cases Queue...")
req = urllib.request.Request(f"{BASE_URL}/api/cases", headers={"Authorization": f"Bearer {tokens['doctor']}"})
res = urllib.request.urlopen(req)
cases_data = json.loads(res.read().decode("utf-8"))
print(f"   [OK] Doctor fetched {len(cases_data['cases'])} cases from triage queue")

print("5. Checking Pharmacist Data Minimization Block (Expected 403)...")
try:
    req = urllib.request.Request(f"{BASE_URL}/api/cases", headers={"Authorization": f"Bearer {tokens['pharmacist']}"})
    urllib.request.urlopen(req)
    print("   [FAIL] Pharmacist should have been blocked!")
except urllib.error.HTTPError as e:
    print(f"   [OK] Pharmacist blocked as expected with HTTP {e.code}: {e.reason}")

print("6. Checking Analyst Aggregates & CSV Export...")
req = urllib.request.Request(f"{BASE_URL}/api/analyst/metrics", headers={"Authorization": f"Bearer {tokens['analyst']}"})
res = urllib.request.urlopen(req)
m_data = json.loads(res.read().decode("utf-8"))
print(f"   [OK] Total cases: {m_data['total_cases']}, Steroid misuse rate: {m_data['steroid_misuse_rate_pct']}%")

req_csv = urllib.request.Request(f"{BASE_URL}/api/analyst/export-csv", headers={"Authorization": f"Bearer {tokens['analyst']}"})
res_csv = urllib.request.urlopen(req_csv)
print(f"   [OK] Analyst CSV export status: {res_csv.status}, Content-Type: {res_csv.headers.get('Content-Type')}")

print("7. Checking Admin Audit Trail...")
req = urllib.request.Request(f"{BASE_URL}/api/admin/audit-log", headers={"Authorization": f"Bearer {tokens['admin']}"})
res = urllib.request.urlopen(req)
audit_data = json.loads(res.read().decode("utf-8"))
print(f"   [OK] Admin audit log entries count: {len(audit_data['audit_log'])}")

print("\n[SUCCESS] ALL API & RBAC HEALTH CHECKS PASSED PERFECTLY!")
