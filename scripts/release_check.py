#!/usr/bin/env python3
import subprocess
import sys
import time
import urllib.request
import urllib.error

def print_step(msg):
    print(f"\n\033[96m===> {msg}\033[0m")

def print_success(msg):
    print(f"\033[92m[OK]\033[0m {msg}")

def print_error(msg):
    print(f"\033[91m[FAIL]\033[0m {msg}", file=sys.stderr)
    sys.exit(1)

def check_service(url, name, expected_status=[200, 401, 403, 404]):
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            status = response.status
    except urllib.error.HTTPError as e:
        status = e.code
    except Exception as e:
        print_error(f"{name} is unreachable at {url}: {e}")
        
    if status in expected_status:
        print_success(f"{name} is reachable (HTTP {status})")
    else:
        print_error(f"{name} returned unexpected HTTP {status}")

def main():
    print_step("Phase 1: Connectivity Checks")
    services = [
        ("http://localhost/api/v1/health", "WAF API (FastAPI)"),
        ("http://localhost:3000", "Juice Shop (Direct)"),
        ("http://localhost:8080", "DVWA (Direct)"),
        ("http://localhost", "Dashboard (Next.js)"),
    ]
    for url, name in services:
        check_service(url, name)
        
    print_step("Phase 2: Backend Tests & Coverage")
    try:
        print("Running pytest inside backend container...")
        subprocess.run(["docker", "compose", "exec", "backend", "pytest", "tests/", "--cov=app", "--cov-report=xml", "--cov-fail-under=80"], check=True)
        print_success("Tests passed and coverage is >= 80%")
    except subprocess.CalledProcessError:
        print_error("Tests failed or coverage is under 80%")

    
    print_step("Phase 3: Traffic Simulation")
    try:
        subprocess.run([sys.executable, "scripts/traffic_simulator.py"], check=True)
        print_success("Traffic simulation passed successfully")
    except subprocess.CalledProcessError:
        print_error("Traffic simulation failed")
        
    print_step("Release Check Complete!")
    print_success("All checks passed. Ready for v1.0-level1 release tagging.")

if __name__ == "__main__":
    main()
