#!/usr/bin/env python3
"""
Specific backend testing for WhatsApp popup, PIN update, and Config endpoints.
Tests the new features implemented in Phase 4 and Phase 5.
"""

import requests
import json
import os
from typing import Dict, Optional, List
import time
from datetime import datetime, timezone, timedelta

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://reseller-chat.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials from review request
ADMIN_PASSWORD = "102030@ab"
CLIENT_WHATSAPP = "11999999999"
CLIENT_PIN = "12"
RESELLER_EMAIL = "michaelrv@gmail.com"
RESELLER_PASSWORD = "ab181818ab"

class WhatsAppConfigTester:
    def __init__(self):
        self.admin_token = None
        self.client_token = None
        self.reseller_token = None
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
    
    def test_admin_login(self) -> bool:
        """Test Admin Login"""
        success, response = self.make_request("POST", "/auth/admin/login", {
            "password": ADMIN_PASSWORD
        })
        
        if success and "token" in response:
            self.admin_token = response["token"]
            self.log_result("Admin Login", True, f"Token received: {response['user_type']}")
            return True
        else:
            self.log_result("Admin Login", False, f"Error: {response}")
            return False
    
    def test_client_register_login(self) -> bool:
        """Test Client Registration/Login"""
        success, response = self.make_request("POST", "/auth/client/login", {
            "whatsapp": CLIENT_WHATSAPP,
            "pin": CLIENT_PIN
        })
        
        if success and "token" in response:
            self.client_token = response["token"]
            self.log_result("Client Register/Login", True, f"Client ID: {response.get('user_data', {}).get('id', 'N/A')}")
            return True
        else:
            self.log_result("Client Register/Login", False, f"Error: {response}")
            return False
    
    def test_reseller_login(self) -> bool:
        """Test Reseller Login (if exists)"""
        success, response = self.make_request("POST", "/resellers/login", {
            "email": RESELLER_EMAIL,
            "password": RESELLER_PASSWORD
        })
        
        if success and "token" in response:
            self.reseller_token = response["token"]
            self.log_result("Reseller Login", True, f"Reseller ID: {response.get('reseller_id', 'N/A')}")
            return True
        else:
            self.log_result("Reseller Login", False, f"Error: {response}")
            return False
    
    def test_whatsapp_popup_status_first_time(self) -> bool:
        """Test GET /users/whatsapp-popup-status - First time (should show)"""
        if not self.client_token:
            self.log_result("WhatsApp Popup Status (First Time)", False, "No client token")
            return False
            
        success, response = self.make_request("GET", "/users/whatsapp-popup-status", token=self.client_token)
        
        if success and "should_show" in response:
            should_show = response["should_show"]
            if should_show:
                self.log_result("WhatsApp Popup Status (First Time)", True, "Correctly shows popup for new user")
                return True
            else:
                self.log_result("WhatsApp Popup Status (First Time)", False, f"Should show popup but got: {response}")
                return False
        else:
            self.log_result("WhatsApp Popup Status (First Time)", False, f"Error: {response}")
            return False
    
    def test_whatsapp_confirm(self) -> bool:
        """Test PUT /users/me/whatsapp-confirm"""
        if not self.client_token:
            self.log_result("WhatsApp Confirm", False, "No client token")
            return False
            
        success, response = self.make_request("PUT", "/users/me/whatsapp-confirm", {
            "whatsapp": CLIENT_WHATSAPP
        }, token=self.client_token)
        
        if success and response.get("ok"):
            self.log_result("WhatsApp Confirm", True, "WhatsApp confirmed successfully")
            return True
        else:
            self.log_result("WhatsApp Confirm", False, f"Error: {response}")
            return False
    
    def test_whatsapp_popup_status_after_confirm(self) -> bool:
        """Test GET /users/whatsapp-popup-status - After confirm (should not show for 7 days)"""
        if not self.client_token:
            self.log_result("WhatsApp Popup Status (After Confirm)", False, "No client token")
            return False
            
        success, response = self.make_request("GET", "/users/whatsapp-popup-status", token=self.client_token)
        
        if success and "should_show" in response:
            should_show = response["should_show"]
            if not should_show:
                days_until_next = response.get("days_until_next", 0)
                self.log_result("WhatsApp Popup Status (After Confirm)", True, 
                              f"Correctly hidden for {7 - days_until_next} days")
                return True
            else:
                self.log_result("WhatsApp Popup Status (After Confirm)", False, 
                              "Should not show popup after recent confirm")
                return False
        else:
            self.log_result("WhatsApp Popup Status (After Confirm)", False, f"Error: {response}")
            return False
    
    def test_pin_update(self) -> bool:
        """Test PUT /users/me/pin"""
        if not self.client_token:
            self.log_result("PIN Update", False, "No client token")
            return False
            
        new_pin = "99"
        success, response = self.make_request("PUT", "/users/me/pin", {
            "pin": new_pin
        }, token=self.client_token)
        
        if success and response.get("ok"):
            self.log_result("PIN Update", True, f"PIN updated to {new_pin}")
            return True
        else:
            self.log_result("PIN Update", False, f"Error: {response}")
            return False
    
    def test_pin_update_invalid(self) -> bool:
        """Test PUT /users/me/pin with invalid PIN (should fail)"""
        if not self.client_token:
            self.log_result("PIN Update (Invalid)", False, "No client token")
            return False
            
        # Test with 3 digits (should fail)
        success, response = self.make_request("PUT", "/users/me/pin", {
            "pin": "123"
        }, token=self.client_token)
        
        if not success and "2 dígitos" in str(response):
            self.log_result("PIN Update (Invalid)", True, "Correctly rejected invalid PIN")
            return True
        else:
            self.log_result("PIN Update (Invalid)", False, f"Should have rejected invalid PIN: {response}")
            return False
    
    def test_config_get_admin(self) -> bool:
        """Test GET /config as Admin - Should return all new fields"""
        if not self.admin_token:
            self.log_result("Config GET (Admin)", False, "No admin token")
            return False
            
        success, response = self.make_request("GET", "/config", token=self.admin_token)
        
        if success:
            # Check for all required fields
            required_fields = ["quick_blocks", "auto_reply", "apps", "pix_key", "allowed_data", "api_integration", "ai_agent"]
            missing_fields = []
            
            for field in required_fields:
                if field not in response:
                    missing_fields.append(field)
            
            if not missing_fields:
                # Check structure of complex fields
                allowed_data = response.get("allowed_data", {})
                api_integration = response.get("api_integration", {})
                ai_agent = response.get("ai_agent", {})
                
                allowed_data_ok = all(key in allowed_data for key in ["cpfs", "emails", "phones", "random_keys"])
                api_integration_ok = all(key in api_integration for key in ["api_url", "api_token", "api_enabled"])
                ai_agent_ok = all(key in ai_agent for key in ["name", "enabled", "llm_provider", "llm_model"])
                
                if allowed_data_ok and api_integration_ok and ai_agent_ok:
                    self.log_result("Config GET (Admin)", True, "All required fields present with correct structure")
                    return True
                else:
                    self.log_result("Config GET (Admin)", False, 
                                  f"Field structure issues - allowed_data: {allowed_data_ok}, api_integration: {api_integration_ok}, ai_agent: {ai_agent_ok}")
                    return False
            else:
                self.log_result("Config GET (Admin)", False, f"Missing fields: {missing_fields}")
                return False
        else:
            self.log_result("Config GET (Admin)", False, f"Error: {response}")
            return False
    
    def test_config_get_reseller(self) -> bool:
        """Test GET /config as Reseller - Should return reseller_configs"""
        if not self.reseller_token:
            self.log_result("Config GET (Reseller)", False, "No reseller token")
            return False
            
        success, response = self.make_request("GET", "/config", token=self.reseller_token)
        
        if success:
            # Should have reseller_id field for reseller configs
            if "reseller_id" in response:
                # Check for all required fields
                required_fields = ["quick_blocks", "auto_reply", "apps", "pix_key", "allowed_data", "api_integration", "ai_agent"]
                missing_fields = []
                
                for field in required_fields:
                    if field not in response:
                        missing_fields.append(field)
                
                if not missing_fields:
                    self.log_result("Config GET (Reseller)", True, f"Reseller config loaded with reseller_id: {response['reseller_id']}")
                    return True
                else:
                    self.log_result("Config GET (Reseller)", False, f"Missing fields: {missing_fields}")
                    return False
            else:
                self.log_result("Config GET (Reseller)", False, "Missing reseller_id in reseller config")
                return False
        else:
            self.log_result("Config GET (Reseller)", False, f"Error: {response}")
            return False
    
    def test_config_put_admin(self) -> bool:
        """Test PUT /config as Admin - Should save all new fields"""
        if not self.admin_token:
            self.log_result("Config PUT (Admin)", False, "No admin token")
            return False
            
        config_data = {
            "quick_blocks": [{"name": "Test Block", "text": "Test message"}],
            "auto_reply": [{"q": "test", "a": "Test response"}],
            "apps": [],
            "pix_key": "test-pix-key-123",
            "allowed_data": {
                "cpfs": ["123.456.789-00"],
                "emails": ["test@example.com"],
                "phones": ["11999999999"],
                "random_keys": ["550e8400-e29b-41d4-a716-446655440000"]
            },
            "api_integration": {
                "api_url": "https://api.test.com",
                "api_token": "test-token-123",
                "api_enabled": True
            },
            "ai_agent": {
                "name": "Test AI Agent",
                "personality": "Helpful and friendly",
                "instructions": "Always be polite",
                "llm_provider": "openai",
                "llm_model": "gpt-4",
                "temperature": 0.8,
                "max_tokens": 1000,
                "mode": "hybrid",
                "active_hours": "9-18",
                "enabled": True,
                "can_access_credentials": False,
                "knowledge_base": "Test knowledge base"
            }
        }
        
        success, response = self.make_request("PUT", "/config", config_data, token=self.admin_token)
        
        if success and response.get("ok"):
            self.log_result("Config PUT (Admin)", True, "Admin config updated successfully")
            return True
        else:
            self.log_result("Config PUT (Admin)", False, f"Error: {response}")
            return False
    
    def test_config_put_reseller(self) -> bool:
        """Test PUT /config as Reseller - Should save to reseller_configs"""
        if not self.reseller_token:
            self.log_result("Config PUT (Reseller)", False, "No reseller token")
            return False
            
        config_data = {
            "quick_blocks": [{"name": "Reseller Block", "text": "Reseller message"}],
            "auto_reply": [{"q": "oi", "a": "Olá da revenda!"}],
            "apps": [],
            "pix_key": "reseller-pix-key-456",
            "allowed_data": {
                "cpfs": ["987.654.321-00"],
                "emails": ["reseller@example.com"],
                "phones": ["11888888888"],
                "random_keys": ["660e8400-e29b-41d4-a716-446655440001"]
            },
            "api_integration": {
                "api_url": "https://reseller-api.test.com",
                "api_token": "reseller-token-456",
                "api_enabled": False
            },
            "ai_agent": {
                "name": "Reseller AI Agent",
                "personality": "Professional and efficient",
                "instructions": "Focus on sales support",
                "llm_provider": "claude",
                "llm_model": "claude-3",
                "temperature": 0.5,
                "max_tokens": 800,
                "mode": "standby",
                "active_hours": "24/7",
                "enabled": False,
                "can_access_credentials": True,
                "knowledge_base": "Reseller knowledge base"
            }
        }
        
        success, response = self.make_request("PUT", "/config", config_data, token=self.reseller_token)
        
        if success and response.get("ok"):
            self.log_result("Config PUT (Reseller)", True, "Reseller config updated successfully")
            return True
        else:
            self.log_result("Config PUT (Reseller)", False, f"Error: {response}")
            return False
    
    def test_config_backward_compatibility(self) -> bool:
        """Test that old configs get default fields automatically"""
        if not self.admin_token:
            self.log_result("Config Backward Compatibility", False, "No admin token")
            return False
            
        # Get config twice to ensure defaults are added
        success1, response1 = self.make_request("GET", "/config", token=self.admin_token)
        time.sleep(1)
        success2, response2 = self.make_request("GET", "/config", token=self.admin_token)
        
        if success1 and success2:
            # Both should have all required fields
            required_fields = ["pix_key", "allowed_data", "api_integration", "ai_agent"]
            
            fields_present_1 = all(field in response1 for field in required_fields)
            fields_present_2 = all(field in response2 for field in required_fields)
            
            if fields_present_1 and fields_present_2:
                self.log_result("Config Backward Compatibility", True, "Default fields added to old configs")
                return True
            else:
                self.log_result("Config Backward Compatibility", False, 
                              f"Missing fields - First: {fields_present_1}, Second: {fields_present_2}")
                return False
        else:
            self.log_result("Config Backward Compatibility", False, f"Error getting config")
            return False
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting WhatsApp & Config Tests")
        print("=" * 50)
        
        tests = [
            self.test_admin_login,
            self.test_client_register_login,
            self.test_reseller_login,
            self.test_whatsapp_popup_status_first_time,
            self.test_whatsapp_confirm,
            self.test_whatsapp_popup_status_after_confirm,
            self.test_pin_update,
            self.test_pin_update_invalid,
            self.test_config_get_admin,
            self.test_config_get_reseller,
            self.test_config_put_admin,
            self.test_config_put_reseller,
            self.test_config_backward_compatibility
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
                time.sleep(0.5)  # Small delay between tests
            except Exception as e:
                self.log_result(test.__name__, False, f"Exception: {str(e)}")
                
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All WhatsApp & Config tests passed!")
        else:
            print(f"⚠️  {total - passed} tests failed. Check the issues above.")
            
        return passed, total, self.test_results

def main():
    """Main test execution"""
    print(f"🔗 Testing backend at: {API_BASE}")
    
    tester = WhatsAppConfigTester()
    passed, total, results = tester.run_all_tests()
    
    # Return results for external processing
    return {
        "passed": passed,
        "total": total,
        "success_rate": (passed / total) * 100 if total > 0 else 0,
        "results": results
    }

if __name__ == "__main__":
    main()