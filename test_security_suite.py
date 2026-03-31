#!/usr/bin/env python3
"""
Security Infrastructure - Comprehensive Test Suite

This script tests all major security features and endpoints.
Run this after deploying to verify everything works.

Usage: python test_security_suite.py
"""

import requests
import json
import sys
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000"  # Main app
BACKEND_URL = "http://localhost:5001"  # Security backend
HOME_URL = "http://localhost:5002"  # Home app

# API Keys (from environment)
API_KEY = "your-api-integration-key"
ADMIN_KEY = "your-admin-api-key"
TURNSTILE_TOKEN = "dummy-token"  # Will be provided by form

class Colors:
    """ANSI color codes"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_test(name):
    """Print test header"""
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"TEST: {name}")
    print(f"{'='*60}{Colors.END}")

def print_pass(msg):
    """Print success message"""
    print(f"{Colors.GREEN}✓ PASS: {msg}{Colors.END}")

def print_fail(msg):
    """Print failure message"""
    print(f"{Colors.RED}✗ FAIL: {msg}{Colors.END}")

def print_warn(msg):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ WARN: {msg}{Colors.END}")

def print_result(response):
    """Print API response"""
    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")

# ============================================================================
# SECURITY BACKEND TESTS
# ============================================================================

def test_backend_health():
    """Test backend is running"""
    print_test("Backend Health Check")
    
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            print_pass("Backend is running")
            return True
        else:
            print_fail(f"Backend returned {response.status_code}")
            return False
    except Exception as e:
        print_fail(f"Could not reach backend: {e}")
        return False


def test_ip_status():
    """Test IP status endpoint"""
    print_test("IP Status Lookup")
    
    test_ip = "192.168.1.100"
    headers = {"X-API-Key": API_KEY}
    
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/ip/status/{test_ip}",
            headers=headers,
            timeout=5
        )
        
        print_result(response)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ip_address') == test_ip:
                print_pass(f"IP status retrieved for {test_ip}")
                return True
        
        print_fail("IP status endpoint failed")
        return False
    
    except Exception as e:
        print_fail(f"Error: {e}")
        return False


def test_report_threat():
    """Test threat reporting"""
    print_test("Report Malicious IP")
    
    headers = {"X-API-Key": API_KEY}
    payload = {
        "ip_address": "10.0.0.50",
        "threat_type": "brute_force_attack",
        "severity": "high",
        "description": "Multiple failed login attempts",
        "service": "main"
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/ip/report-threat",
            json=payload,
            headers=headers,
            timeout=5
        )
        
        print_result(response)
        
        if response.status_code == 201:
            data = response.json()
            if data.get('threat_level') in ['blocked', 'quarantined', 'suspicious']:
                print_pass("Threat reported and IP threat level updated")
                return True
        
        print_fail("Threat reporting failed")
        return False
    
    except Exception as e:
        print_fail(f"Error: {e}")
        return False


def test_block_ip():
    """Test manual IP blocking"""
    print_test("Block IP Address")
    
    headers = {"X-Admin-Key": ADMIN_KEY}
    payload = {
        "reason": "test_block",
        "admin_email": "admin@test.local"
    }
    
    test_ip = "203.0.113.50"
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/admin/ip/{test_ip}/block",
            json=payload,
            headers=headers,
            timeout=5
        )
        
        print_result(response)
        
        if response.status_code == 200:
            print_pass(f"IP {test_ip} blocked successfully")
            
            # Verify block
            verify_headers = {"X-API-Key": API_KEY}
            verify = requests.get(
                f"{BACKEND_URL}/api/ip/status/{test_ip}",
                headers=verify_headers,
                timeout=5
            )
            
            if verify.json().get('is_blocked'):
                print_pass("IP block verification successful")
                return True
        
        print_fail("IP blocking failed")
        return False
    
    except Exception as e:
        print_fail(f"Error: {e}")
        return False


def test_get_blocked_list():
    """Test getting blocklist"""
    print_test("Get Blocked IP List")
    
    headers = {"X-Admin-Key": ADMIN_KEY}
    
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/admin/blocked-list",
            headers=headers,
            timeout=5
        )
        
        print_result(response)
        
        if response.status_code == 200:
            data = response.json()
            count = data.get('count', 0)
            print_pass(f"Retrieved {count} blocked IPs")
            return True
        
        print_fail("Failed to get blocked list")
        return False
    
    except Exception as e:
        print_fail(f"Error: {e}")
        return False


def test_dashboard_overview():
    """Test dashboard overview"""
    print_test("Dashboard Overview")
    
    headers = {"X-API-Key": API_KEY}
    
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/dashboard/overview",
            headers=headers,
            timeout=5
        )
        
        print_result(response)
        
        if response.status_code == 200:
            data = response.json()
            overview = data.get('overview', {})
            ips = data.get('ips', {})
            print_pass(f"Dashboard loaded - {ips.get('total', 0)} IPs tracked")
            return True
        
        print_fail("Dashboard overview failed")
        return False
    
    except Exception as e:
        print_fail(f"Error: {e}")
        return False


# ============================================================================
# MAIN APP TESTS
# ============================================================================

def test_scanner_detection():
    """Test scanner detection (Burp Suite)"""
    print_test("Scanner Detection (Burp Suite)")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows; U; BurpSuite/2023; like Safari)",
    }
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/test",
            headers=headers,
            timeout=5
        )
        
        print_result(response)
        
        if response.status_code == 403:
            print_pass("Burp Suite scanner detected and blocked (403)")
            return True
        else:
            print_warn(f"Expected 403, got {response.status_code}")
            return False
    
    except Exception as e:
        print_fail(f"Error: {e}")
        return False


def test_sql_injection_detection():
    """Test SQL injection detection"""
    print_test("SQL Injection Detection")
    
    payload = {
        "input": "normal' OR '1'='1"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/test",
            json=payload,
            timeout=5
        )
        
        print_result(response)
        
        if response.status_code == 400:
            data = response.json()
            if 'SQL' in str(data):
                print_pass("SQL injection detected and blocked (400)")
                return True
        
        print_warn(f"Expected 400 with SQL detection, got {response.status_code}")
        return False
    
    except Exception as e:
        print_fail(f"Error: {e}")
        return False


def test_xss_detection():
    """Test XSS detection"""
    print_test("XSS Attack Detection")
    
    payload = {
        "input": "<script>alert('xss')</script>"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/test",
            json=payload,
            timeout=5
        )
        
        print_result(response)
        
        if response.status_code == 400:
            print_pass("XSS attack detected and blocked (400)")
            return True
        else:
            print_warn(f"Expected 400, got {response.status_code}")
            return False
    
    except Exception as e:
        print_fail(f"Error: {e}")
        return False


def test_input_sanitization():
    """Test input sanitization"""
    print_test("Input Sanitization")
    
    payload = {
        "email": "test@example.com",
        "message": "This is a normal message"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/test",
            json=payload,
            timeout=5
        )
        
        print_result(response)
        
        if response.status_code in [200, 400]:
            print_pass("Input sanitization working")
            return True
        
        print_fail(f"Got unexpected status {response.status_code}")
        return False
    
    except Exception as e:
        print_fail(f"Error: {e}")
        return False


# ============================================================================
# HOME PAGE TESTS
# ============================================================================

def test_contact_form_rate_limit():
    """Test rate limiting on contact form"""
    print_test("Contact Form Rate Limiting")
    
    # Try 6 rapid requests (limit is 5/minute)
    success_count = 0
    blocked_count = 0
    
    for i in range(6):
        try:
            response = requests.post(
                f"{HOME_URL}/contact/submit",
                data={
                    "name": f"Test {i}",
                    "email": "test@example.com",
                    "message": f"Test message {i}",
                    "cf-turnstile-response": TURNSTILE_TOKEN
                },
                timeout=5
            )
            
            if response.status_code == 200:
                success_count += 1
            elif response.status_code == 429:
                blocked_count += 1
            
            print(f"Request {i+1}: {response.status_code}")
        
        except Exception as e:
            print_fail(f"Request {i+1} error: {e}")
    
    if blocked_count > 0:
        print_pass(f"Rate limiting working - {blocked_count} requests blocked")
        return True
    else:
        print_warn("Rate limiting not triggered (may not be enforced yet)")
        return False


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Run all tests"""
    print(f"\n{Colors.BLUE}{'='*60}")
    print("SECURITY INFRASTRUCTURE TEST SUITE")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}{Colors.END}\n")
    
    results = []
    
    # Backend Tests
    print(f"\n{Colors.BLUE}[SECURITY BACKEND TESTS]{Colors.END}")
    results.append(("Backend Health", test_backend_health()))
    results.append(("IP Status Lookup", test_ip_status()))
    results.append(("Report Threat", test_report_threat()))
    results.append(("Block IP", test_block_ip()))
    results.append(("Get Blocked List", test_get_blocked_list()))
    results.append(("Dashboard Overview", test_dashboard_overview()))
    
    # Main App Tests
    print(f"\n{Colors.BLUE}[MAIN APP SECURITY TESTS]{Colors.END}")
    results.append(("Scanner Detection", test_scanner_detection()))
    results.append(("SQL Injection Detection", test_sql_injection_detection()))
    results.append(("XSS Detection", test_xss_detection()))
    results.append(("Input Sanitization", test_input_sanitization()))
    
    # Home Page Tests
    print(f"\n{Colors.BLUE}[HOME PAGE SECURITY TESTS]{Colors.END}")
    results.append(("Rate Limiting", test_contact_form_rate_limit()))
    
    # Summary
    print(f"\n{Colors.BLUE}{'='*60}")
    print("TEST RESULTS SUMMARY")
    print(f"{'='*60}{Colors.END}\n")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{Colors.GREEN}PASS{Colors.END}" if result else f"{Colors.RED}FAIL{Colors.END}"
        print(f"  {test_name:<30} {status}")
    
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print(f"{Colors.GREEN}All tests passed! Security infrastructure is working.{Colors.END}")
        return 0
    else:
        print(f"{Colors.RED}Some tests failed. Review output above.{Colors.END}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
