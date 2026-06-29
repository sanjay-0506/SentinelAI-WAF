#!/usr/bin/env python3
import urllib.request
import urllib.error
import json
import sys
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

def print_success(msg):
    print(f"\033[92m[OK]\033[0m {msg}")

def print_failure(msg):
    print(f"\033[91m[FAIL]\033[0m {msg}", file=sys.stderr)

def print_info(msg):
    print(f"\033[94m[INFO]\033[0m {msg}")

NORMAL_CASES = [
    {"name": "Juice Shop: Normal Homepage Request", "url": "http://localhost:3000/", "method": "GET", "headers": {"User-Agent": "Mozilla/5.0"}, "data": None, "expected_decision": "allowed"},
    {"name": "Juice Shop: Search for Apple", "url": "http://localhost:3000/rest/products/search?q=apple", "method": "GET", "headers": {}, "data": None, "expected_decision": "allowed"},
    {"name": "DVWA: Normal Login Page Request", "url": "http://localhost:8080/login.php", "method": "GET", "headers": {}, "data": None, "expected_decision": "allowed"},
]

ATTACK_CASES = [
    # SQLI
    {"name": "SQL Injection - UNION SELECT", "url": "http://localhost:3000/rest/products/search?q=apple%27%20UNION%20SELECT%20null,id,email,password%20FROM%20users--", "method": "GET", "headers": {}, "data": None, "expected_decision": "blocked"},
    {"name": "SQL Injection - Time Based SLEEP", "url": "http://localhost:3000/rest/products/search?q=apple%27%20and%20sleep(5)--", "method": "GET", "headers": {}, "data": None, "expected_decision": "blocked"},
    {"name": "SQL Injection - Stacked Queries", "url": "http://localhost:3000/rest/products/search?q=apple%27;%20DROP%20TABLE%20users--", "method": "GET", "headers": {}, "data": None, "expected_decision": "blocked"},
    # XSS
    {"name": "XSS - Script Tag", "url": "http://localhost:3000/rest/products/search?q=%3Cscript%3Ealert(document.cookie)%3C/script%3E", "method": "GET", "headers": {}, "data": None, "expected_decision": "blocked"},
    {"name": "XSS - img src Injection", "url": "http://localhost:3000/rest/products/search?q=%3Cimg%20src=x%20onerror=alert(1)%3E", "method": "GET", "headers": {}, "data": None, "expected_decision": "blocked"},
    # PATH TRAVERSAL
    {"name": "Path Traversal - Backslash Sequence", "url": "http://localhost:8080/vulnerabilities/fi/?page=..%5C..%5C..%5Cwindows%5Cwin.ini", "method": "GET", "headers": {}, "data": None, "expected_decision": "blocked"},
    {"name": "Path Traversal - Null Byte", "url": "http://localhost:8080/vulnerabilities/fi/?page=%2e%2e/%2e%2e/%2e%2e/%2e%2e/etc/passwd%00.html", "method": "GET", "headers": {}, "data": None, "expected_decision": "blocked"},
    # COMMAND INJECTION
    {"name": "Command Injection - Semicolon", "url": "http://localhost:8080/vulnerabilities/exec/", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": "ip=127.0.0.1%3B%20whoami&Submit=Submit", "expected_decision": "blocked"},
    {"name": "Command Injection - Pipe Operator", "url": "http://localhost:8080/vulnerabilities/exec/", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": "ip=127.0.0.1%20%7C%20whoami&Submit=Submit", "expected_decision": "blocked"}
]

def run_test(case):
    url = case["url"]
    method = case["method"]
    headers = case["headers"]
    data_str = case["data"]
    expected = case["expected_decision"]

    data_bytes = data_str.encode('utf-8') if data_str else None
    req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            status = response.status
            response.read()
        decision = "allowed"
    except urllib.error.HTTPError as e:
        status = e.code
        decision = "blocked" if status == 403 else "allowed"
        e.read()
    except Exception as e:
        return False, f"Connection failed: {e}"

    if decision == expected:
        return True, "Behaved as expected"
    else:
        return False, f"Unexpected! Expected {expected}, Got {decision}"

def main():
    print_info("Starting Level 1 Finalization Traffic Simulator...")
    num_normal = random.randint(200, 500)
    num_attacks = random.randint(100, 300)
    
    print_info(f"Targeting: {num_normal} Normal Requests, {num_attacks} Attack Requests")
    
    tasks = []
    for _ in range(num_normal):
        tasks.append(random.choice(NORMAL_CASES))
    for _ in range(num_attacks):
        tasks.append(random.choice(ATTACK_CASES))
        
    random.shuffle(tasks)
    
    passed = 0
    failed = 0
    
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(run_test, task): task for task in tasks}
        for future in as_completed(futures):
            success, msg = future.result()
            if success:
                passed += 1
            else:
                failed += 1
                
    duration = time.time() - start_time
    print("\n================ SIMULATION REPORT ================")
    print(f"Total Requests: {num_normal + num_attacks}")
    print(f"Passed Validations: {passed}")
    print(f"Failed Validations: {failed}")
    print(f"Duration: {duration:.2f} seconds")
    print(f"RPS: {(num_normal + num_attacks)/duration:.2f}")
    
    time.sleep(2)  # Wait for stats processing
    try:
        with urllib.request.urlopen("http://localhost/api/v1/stats", timeout=5) as response:
            stats = json.loads(response.read().decode('utf-8'))
            print("\n================ WAF STATISTICS ================")
            print(f"Total Processed: {stats.get('total_requests')}")
            print(f"Blocked:         {stats.get('blocked')}")
            print(f"Allowed:         {stats.get('allowed')}")
            print("================================================")
            
            if stats.get('blocked', 0) == 0 or stats.get('allowed', 0) == 0:
                print_failure("ERROR: WAF Statistics show 0 blocked or 0 allowed requests.")
                sys.exit(1)
    except Exception as e:
        print_failure(f"Could not retrieve WAF stats: {e}")
        sys.exit(1)
        
    if failed > 0:
        print_failure(f"Simulation failed with {failed} unexpected behaviors.")
        sys.exit(1)
        
    print_success("Simulation completed successfully! All traffic handled correctly.")
    sys.exit(0)

if __name__ == "__main__":
    main()
