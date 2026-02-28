import requests
import json

schedulers = [6789, 6790, 6791]
executors = [9876, 9877, 9878]

def check_status(port, name):
    try:
        response = requests.get(f"http://127.0.0.1:{port}/status", timeout=2)
        if response.status_code == 200:
            print(f"[{name}] Port {port}: ONLINE")
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        else:
            print(f"[{name}] Port {port}: ERROR {response.status_code}")
    except Exception as e:
        print(f"[{name}] Port {port}: OFFLINE ({e})")

print("Checking Schedulers...")
for port in schedulers:
    check_status(port, "Scheduler")

print("\nChecking Executors...")
for port in executors:
    check_status(port, "Executor")
