#!/usr/bin/env python3
"""
Specific test for the ajuda.vip domain login issue.
Tests the multi-tenant system focusing on the reported problem.
"""

import requests
import json
import os
from typing import Dict, Optional, List

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cyberchat-1.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials from the issue
ADMIN_PASSWORD = "102030@ab"
REPORTED_EMAIL = "michael@gmail.com"
REPORTED_PASSWORD = "ab181818ab"
REPORTED_DOMAIN = "ajuda.vip"

class DomainIssueTester:
    def __init__(self):
        self.admin_token = None
        self.test_results = []
        
    def log_result(self, test_name: str, success: bool, message: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status} {test_name}"
        if message:
            result += f" - {message}"
        print(result)
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message
        })
        
    def make_request(self, method: str, endpoint: str, data: dict = None, 
                    token: str = None, headers: dict = None) -> tuple[bool, dict]:
        """Make HTTP request with error handling"""
        url = f"{API_BASE}{endpoint}"
        
        request_headers = {"Content-Type": "application/json"}
        if token:
            request_headers["Authorization"] = f"Bearer {token}"
        if headers:
            request_headers.update(headers)
            
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=request_headers, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers=request_headers, timeout=30)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data, headers=request_headers, timeout=30)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=request_headers, timeout=30)
            else:
                return False, {"error": f"Unsupported method: {method}"}
                
            return response.status_code < 400, response.json() if response.text else {}
            
        except requests.exceptions.RequestException as e:
            return False, {"error": str(e)}
        except json.JSONDecodeError:
            return False, {"error": "Invalid JSON response"}
            
    def test_1_admin_login(self) -> bool:
        """Test 1: Admin Master Authentication"""
        print(f"\n🔐 Testing admin login with password: {ADMIN_PASSWORD}")
        
        success, response = self.make_request("POST", "/auth/admin/login", {
            "password": ADMIN_PASSWORD
        })
        
        if success and "token" in response:
            self.admin_token = response["token"]
            self.log_result("Admin Login", True, f"Token received successfully")
            return True
        else:
            self.log_result("Admin Login", False, f"Error: {response}")
            return False
            
    def test_2_list_all_resellers(self) -> bool:
        """Test 2: List all resellers to find ajuda.vip"""
        print(f"\n📋 Listing all resellers to find domain: {REPORTED_DOMAIN}")
        
        if not self.admin_token:
            self.log_result("List All Resellers", False, "No admin token available")
            return False
            
        success, response = self.make_request("GET", "/resellers", token=self.admin_token)
        
        if success and isinstance(response, list):
            print(f"Found {len(response)} resellers:")
            
            ajuda_vip_resellers = []
            for reseller in response:
                print(f"  - ID: {reseller.get('id', 'N/A')}")
                print(f"    Name: {reseller.get('name', 'N/A')}")
                print(f"    Email: {reseller.get('email', 'N/A')}")
                print(f"    Domain: {reseller.get('domain', 'N/A')}")
                print(f"    Custom Domain: {reseller.get('custom_domain', 'N/A')}")
                print(f"    Parent ID: {reseller.get('parent_id', 'N/A')}")
                print(f"    Level: {reseller.get('level', 'N/A')}")
                print("    ---")
                
                # Check if this reseller has ajuda.vip domain
                if (reseller.get('custom_domain') == REPORTED_DOMAIN or 
                    reseller.get('domain') == REPORTED_DOMAIN):
                    ajuda_vip_resellers.append(reseller)
            
            if ajuda_vip_resellers:
                if len(ajuda_vip_resellers) == 1:
                    reseller = ajuda_vip_resellers[0]
                    self.log_result("List All Resellers", True, 
                                  f"Found 1 reseller with domain {REPORTED_DOMAIN}: {reseller.get('email', 'N/A')}")
                    return True
                else:
                    self.log_result("List All Resellers", False, 
                                  f"PROBLEM: Found {len(ajuda_vip_resellers)} resellers with domain {REPORTED_DOMAIN} - DOMAIN CONFLICT!")
                    return False
            else:
                self.log_result("List All Resellers", False, 
                              f"No reseller found with domain {REPORTED_DOMAIN}")
                return False
        else:
            self.log_result("List All Resellers", False, f"Error: {response}")
            return False
            
    def test_3_find_ajuda_vip_reseller(self) -> Optional[Dict]:
        """Test 3: Find the specific reseller for ajuda.vip"""
        print(f"\n🔍 Finding reseller details for domain: {REPORTED_DOMAIN}")
        
        if not self.admin_token:
            self.log_result("Find ajuda.vip Reseller", False, "No admin token available")
            return None
            
        success, response = self.make_request("GET", "/resellers", token=self.admin_token)
        
        if success and isinstance(response, list):
            for reseller in response:
                if (reseller.get('custom_domain') == REPORTED_DOMAIN or 
                    reseller.get('domain') == REPORTED_DOMAIN):
                    
                    print(f"🎯 FOUND RESELLER FOR {REPORTED_DOMAIN}:")
                    print(f"  ID: {reseller.get('id')}")
                    print(f"  Name: {reseller.get('name')}")
                    print(f"  Email: {reseller.get('email')}")
                    print(f"  Domain: {reseller.get('domain')}")
                    print(f"  Custom Domain: {reseller.get('custom_domain')}")
                    print(f"  Parent ID: {reseller.get('parent_id')}")
                    print(f"  Level: {reseller.get('level')}")
                    
                    self.log_result("Find ajuda.vip Reseller", True, 
                                  f"Email: {reseller.get('email')}, ID: {reseller.get('id')}")
                    return reseller
            
            self.log_result("Find ajuda.vip Reseller", False, 
                          f"No reseller found with domain {REPORTED_DOMAIN}")
            return None
        else:
            self.log_result("Find ajuda.vip Reseller", False, f"Error: {response}")
            return None
            
    def test_4_test_reseller_login_with_found_email(self, reseller: Dict) -> bool:
        """Test 4: Test login with the email found for ajuda.vip"""
        if not reseller:
            self.log_result("Test Reseller Login (Found Email)", False, "No reseller data available")
            return False
            
        found_email = reseller.get('email')
        print(f"\n🔑 Testing reseller login with found email: {found_email}")
        print(f"    Password: {REPORTED_PASSWORD}")
        
        success, response = self.make_request("POST", "/resellers/login", {
            "email": found_email,
            "password": REPORTED_PASSWORD
        })
        
        if success and "token" in response:
            self.log_result("Test Reseller Login (Found Email)", True, 
                          f"Login successful with email: {found_email}")
            return True
        else:
            self.log_result("Test Reseller Login (Found Email)", False, 
                          f"Login failed with email {found_email}: {response}")
            return False
            
    def test_5_test_reseller_login_with_reported_email(self) -> bool:
        """Test 5: Test login with the originally reported email"""
        print(f"\n🔑 Testing reseller login with reported email: {REPORTED_EMAIL}")
        print(f"    Password: {REPORTED_PASSWORD}")
        
        success, response = self.make_request("POST", "/resellers/login", {
            "email": REPORTED_EMAIL,
            "password": REPORTED_PASSWORD
        })
        
        if success and "token" in response:
            self.log_result("Test Reseller Login (Reported Email)", True, 
                          f"Login successful with reported email: {REPORTED_EMAIL}")
            return True
        else:
            self.log_result("Test Reseller Login (Reported Email)", False, 
                          f"Login failed with reported email {REPORTED_EMAIL}: {response}")
            return False
            
    def test_6_test_tenant_middleware(self) -> bool:
        """Test 6: Test tenant middleware with Host header"""
        print(f"\n🌐 Testing tenant middleware with Host: {REPORTED_DOMAIN}")
        
        # Test with Host header to simulate ajuda.vip domain access
        headers = {"Host": REPORTED_DOMAIN}
        
        success, response = self.make_request("GET", "/agents", 
                                            headers=headers, token=self.admin_token)
        
        if success:
            agent_count = len(response) if isinstance(response, list) else 0
            self.log_result("Test Tenant Middleware", True, 
                          f"Middleware working - returned {agent_count} agents for domain {REPORTED_DOMAIN}")
            return True
        else:
            self.log_result("Test Tenant Middleware", False, 
                          f"Middleware test failed: {response}")
            return False
            
    def test_7_check_domain_conflicts(self) -> bool:
        """Test 7: Check for multiple resellers with same domain"""
        print(f"\n⚠️  Checking for domain conflicts with: {REPORTED_DOMAIN}")
        
        if not self.admin_token:
            self.log_result("Check Domain Conflicts", False, "No admin token available")
            return False
            
        success, response = self.make_request("GET", "/resellers", token=self.admin_token)
        
        if success and isinstance(response, list):
            matching_resellers = []
            
            for reseller in response:
                if (reseller.get('custom_domain') == REPORTED_DOMAIN or 
                    reseller.get('domain') == REPORTED_DOMAIN):
                    matching_resellers.append(reseller)
            
            if len(matching_resellers) == 0:
                self.log_result("Check Domain Conflicts", False, 
                              f"No resellers found with domain {REPORTED_DOMAIN}")
                return False
            elif len(matching_resellers) == 1:
                self.log_result("Check Domain Conflicts", True, 
                              f"No conflicts - only 1 reseller has domain {REPORTED_DOMAIN}")
                return True
            else:
                print(f"🚨 DOMAIN CONFLICT DETECTED! {len(matching_resellers)} resellers have domain {REPORTED_DOMAIN}:")
                for i, reseller in enumerate(matching_resellers, 1):
                    print(f"  {i}. ID: {reseller.get('id')}, Email: {reseller.get('email')}")
                
                self.log_result("Check Domain Conflicts", False, 
                              f"CONFLICT: {len(matching_resellers)} resellers have domain {REPORTED_DOMAIN}")
                return False
        else:
            self.log_result("Check Domain Conflicts", False, f"Error: {response}")
            return False
            
    def run_domain_issue_tests(self):
        """Run all domain-specific tests"""
        print("🚀 Starting Domain Issue Investigation")
        print(f"🎯 Target Domain: {REPORTED_DOMAIN}")
        print(f"📧 Reported Email: {REPORTED_EMAIL}")
        print(f"🔒 Reported Password: {REPORTED_PASSWORD}")
        print("=" * 60)
        
        # Step 1: Admin login
        if not self.test_1_admin_login():
            print("❌ Cannot proceed without admin access")
            return
            
        # Step 2: List all resellers
        self.test_2_list_all_resellers()
        
        # Step 3: Find specific reseller
        reseller = self.test_3_find_ajuda_vip_reseller()
        
        # Step 4: Test login with found email
        if reseller:
            self.test_4_test_reseller_login_with_found_email(reseller)
        
        # Step 5: Test login with reported email
        self.test_5_test_reseller_login_with_reported_email()
        
        # Step 6: Test tenant middleware
        self.test_6_test_tenant_middleware()
        
        # Step 7: Check for domain conflicts
        self.test_7_check_domain_conflicts()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 DOMAIN ISSUE INVESTIGATION SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Tests Passed: {passed}/{total}")
        
        # Analyze results and provide recommendations
        self.analyze_and_recommend()
        
    def analyze_and_recommend(self):
        """Analyze test results and provide specific recommendations"""
        print("\n🔍 ANALYSIS AND RECOMMENDATIONS:")
        print("-" * 40)
        
        # Check if we found the reseller
        found_reseller = any("Find ajuda.vip Reseller" in result["test"] and result["success"] 
                           for result in self.test_results)
        
        # Check if there are domain conflicts
        has_conflicts = any("Check Domain Conflicts" in result["test"] and not result["success"] 
                          for result in self.test_results)
        
        # Check login results
        found_email_login = any("Test Reseller Login (Found Email)" in result["test"] and result["success"] 
                              for result in self.test_results)
        reported_email_login = any("Test Reseller Login (Reported Email)" in result["test"] and result["success"] 
                                 for result in self.test_results)
        
        if not found_reseller:
            print("❌ PROBLEM: No reseller found with domain ajuda.vip")
            print("   SOLUTION: Create a reseller with custom_domain = 'ajuda.vip'")
            
        elif has_conflicts:
            print("❌ PROBLEM: Multiple resellers have the same domain ajuda.vip")
            print("   SOLUTION: Remove duplicate domains or use unique domains")
            
        elif found_reseller and not found_email_login and not reported_email_login:
            print("❌ PROBLEM: Reseller exists but login fails with both emails")
            print("   POSSIBLE CAUSES:")
            print("   1. Incorrect password")
            print("   2. Password hash mismatch")
            print("   3. Email mismatch")
            print("   SOLUTION: Reset password or verify email")
            
        elif found_reseller and found_email_login and not reported_email_login:
            print("⚠️  PROBLEM: Login works with database email but not reported email")
            print("   CAUSE: Email mismatch between database and user expectation")
            print("   SOLUTION: Update reseller email or inform user of correct email")
            
        elif found_reseller and found_email_login and reported_email_login:
            print("✅ SUCCESS: Login works with both emails")
            print("   The system is working correctly")
            
        else:
            print("🤔 MIXED RESULTS: Check individual test results above")

def main():
    """Main test execution"""
    print(f"🔗 Testing backend at: {API_BASE}")
    
    tester = DomainIssueTester()
    tester.run_domain_issue_tests()

if __name__ == "__main__":
    main()