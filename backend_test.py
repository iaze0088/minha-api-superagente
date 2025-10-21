#!/usr/bin/env python3
"""
TESTE COMPLETO DO BACKEND - APÓS CORREÇÕES CRÍTICAS
Testa todas as rotas críticas: autenticação, atendentes, agentes IA, departamentos, config, revendas
"""

import requests
import json
import os
from typing import Dict, Optional, List
import time

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://supportdesk-pro.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
ADMIN_PASSWORD = "102030@ab"  # From .env file

class ComprehensiveBackendTester:
    def __init__(self):
        self.admin_token = None
        self.agent_token = None
        self.client_token = None
        self.reseller_token = None
        self.created_agents = []
        self.created_ai_agents = []
        self.created_departments = []
        self.created_resellers = []
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
            
    # ============================================
    # TESTES DE AUTENTICAÇÃO
    # ============================================
    
    def test_admin_login(self) -> bool:
        """Test 1: POST /api/auth/admin/login (senha: 102030@ab)"""
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
    
    def test_agent_login(self) -> bool:
        """Test 2: POST /api/auth/agent/login"""
        # First create an agent
        if not self.admin_token:
            self.log_result("Agent Login", False, "Admin token required")
            return False
            
        agent_data = {
            "name": "Agente Teste",
            "login": "agente_teste",
            "password": "123456",
            "avatar": ""
        }
        
        success, response = self.make_request("POST", "/agents", agent_data, self.admin_token)
        if not success:
            self.log_result("Agent Login", False, f"Failed to create agent: {response}")
            return False
            
        agent_id = response.get("id")
        if agent_id:
            self.created_agents.append(agent_id)
        
        # Now test login
        login_data = {
            "login": "agente_teste",
            "password": "123456"
        }
        
        success, response = self.make_request("POST", "/auth/agent/login", login_data)
        
        if success and "token" in response:
            self.agent_token = response["token"]
            self.log_result("Agent Login", True, f"Agent logged in: {response.get('user_data', {}).get('name')}")
            return True
        else:
            self.log_result("Agent Login", False, f"Error: {response}")
            return False
    
    def test_client_login(self) -> bool:
        """Test 3: POST /api/auth/client/login"""
        login_data = {
            "whatsapp": "11999999999",
            "pin": "12"
        }
        
        success, response = self.make_request("POST", "/auth/client/login", login_data)
        
        if success and "token" in response:
            self.client_token = response["token"]
            self.log_result("Client Login", True, f"Client logged in: {response.get('user_data', {}).get('whatsapp')}")
            return True
        else:
            self.log_result("Client Login", False, f"Error: {response}")
            return False
            
    # ============================================
    # TESTES DE ATENDENTES
    # ============================================
    
    def test_list_agents(self) -> bool:
        """Test 4: GET /api/agents (listar atendentes)"""
        if not self.admin_token:
            self.log_result("List Agents", False, "Admin token required")
            return False
            
        success, response = self.make_request("GET", "/agents", token=self.admin_token)
        
        if success and isinstance(response, list):
            count = len(response)
            self.log_result("List Agents", True, f"Found {count} agents")
            return True
        else:
            self.log_result("List Agents", False, f"Error: {response}")
            return False
    
    def test_create_agent(self) -> bool:
        """Test 5: POST /api/agents (criar atendente)"""
        if not self.admin_token:
            self.log_result("Create Agent", False, "Admin token required")
            return False
            
        agent_data = {
            "name": "Novo Agente Teste",
            "login": "novo_agente",
            "password": "senha123",
            "avatar": ""
        }
        
        success, response = self.make_request("POST", "/agents", agent_data, self.admin_token)
        
        if success and response.get("ok"):
            agent_id = response.get("id")
            if agent_id:
                self.created_agents.append(agent_id)
            self.log_result("Create Agent", True, f"Agent created with ID: {agent_id}")
            return True
        else:
            self.log_result("Create Agent", False, f"Error: {response}")
            return False
            
    # ============================================
    # TESTES DE AGENTES IA (PRIORIDADE ALTA)
    # ============================================
    
    def test_list_ai_agents(self) -> bool:
        """Test 6: GET /api/ai/agents (listar agentes IA)"""
        if not self.admin_token:
            self.log_result("List AI Agents", False, "Admin token required")
            return False
            
        success, response = self.make_request("GET", "/ai/agents", token=self.admin_token)
        
        if success and isinstance(response, list):
            count = len(response)
            self.log_result("List AI Agents", True, f"Found {count} AI agents")
            return True
        else:
            self.log_result("List AI Agents", False, f"Error: {response}")
            return False
    
    def test_create_ai_agent(self) -> bool:
        """Test 7: POST /api/ai/agents (criar agente IA)"""
        if not self.admin_token:
            self.log_result("Create AI Agent", False, "Admin token required")
            return False
            
        ai_agent_data = {
            "name": "Agente IA Teste",
            "description": "Agente de teste para validação",
            "llm_provider": "openai",
            "llm_model": "gpt-4o-mini"
        }
        
        success, response = self.make_request("POST", "/ai/agents", ai_agent_data, self.admin_token)
        
        if success and "id" in response:
            agent_id = response.get("id")
            self.created_ai_agents.append(agent_id)
            self.log_result("Create AI Agent", True, f"AI Agent created: {response.get('name')} (ID: {agent_id})")
            return True
        else:
            self.log_result("Create AI Agent", False, f"Error: {response}")
            return False
    
    def test_update_ai_agent(self) -> bool:
        """Test 8: PUT /api/ai/agents/{id} (atualizar agente)"""
        if not self.admin_token or not self.created_ai_agents:
            self.log_result("Update AI Agent", False, "Admin token or AI agent required")
            return False
            
        agent_id = self.created_ai_agents[0]
        update_data = {
            "name": "Agente IA Atualizado",
            "description": "Descrição atualizada",
            "temperature": 0.8
        }
        
        success, response = self.make_request("PUT", f"/ai/agents/{agent_id}", update_data, self.admin_token)
        
        if success and "id" in response:
            self.log_result("Update AI Agent", True, f"AI Agent updated: {response.get('name')}")
            return True
        else:
            self.log_result("Update AI Agent", False, f"Error: {response}")
            return False
    
    def test_delete_ai_agent(self) -> bool:
        """Test 9: DELETE /api/ai/agents/{id} (deletar agente)"""
        if not self.admin_token or not self.created_ai_agents:
            self.log_result("Delete AI Agent", False, "Admin token or AI agent required")
            return False
            
        agent_id = self.created_ai_agents[-1]  # Delete the last one
        
        success, response = self.make_request("DELETE", f"/ai/agents/{agent_id}", token=self.admin_token)
        
        if success and response.get("ok"):
            self.created_ai_agents.remove(agent_id)
            self.log_result("Delete AI Agent", True, f"AI Agent deleted: {agent_id}")
            return True
        else:
            self.log_result("Delete AI Agent", False, f"Error: {response}")
            return False
            
    # ============================================
    # TESTES DE DEPARTAMENTOS (PRIORIDADE ALTA)
    # ============================================
    
    def test_list_departments(self) -> bool:
        """Test 10: GET /api/ai/departments (listar departamentos)"""
        if not self.admin_token:
            self.log_result("List Departments", False, "Admin token required")
            return False
            
        success, response = self.make_request("GET", "/ai/departments", token=self.admin_token)
        
        if success and isinstance(response, list):
            count = len(response)
            self.log_result("List Departments", True, f"Found {count} departments")
            return True
        else:
            self.log_result("List Departments", False, f"Error: {response}")
            return False
    
    def test_create_department(self) -> bool:
        """Test 11: POST /api/ai/departments (criar departamento)"""
        if not self.admin_token:
            self.log_result("Create Department", False, "Admin token required")
            return False
            
        dept_data = {
            "name": "Suporte Técnico",
            "description": "Departamento de suporte técnico",
            "is_default": True,
            "timeout_seconds": 120
        }
        
        success, response = self.make_request("POST", "/ai/departments", dept_data, self.admin_token)
        
        if success and "id" in response:
            dept_id = response.get("id")
            self.created_departments.append(dept_id)
            self.log_result("Create Department", True, f"Department created: {response.get('name')} (ID: {dept_id})")
            return True
        else:
            self.log_result("Create Department", False, f"Error: {response}")
            return False
    
    def test_update_department(self) -> bool:
        """Test 12: PUT /api/ai/departments/{id} (atualizar)"""
        if not self.admin_token or not self.created_departments:
            self.log_result("Update Department", False, "Admin token or department required")
            return False
            
        dept_id = self.created_departments[0]
        update_data = {
            "name": "Suporte Técnico Atualizado",
            "description": "Descrição atualizada do departamento",
            "timeout_seconds": 180
        }
        
        success, response = self.make_request("PUT", f"/ai/departments/{dept_id}", update_data, self.admin_token)
        
        if success and "id" in response:
            self.log_result("Update Department", True, f"Department updated: {response.get('name')}")
            return True
        else:
            self.log_result("Update Department", False, f"Error: {response}")
            return False
    
    def test_delete_department(self) -> bool:
        """Test 13: DELETE /api/ai/departments/{id} (deletar)"""
        if not self.admin_token or not self.created_departments:
            self.log_result("Delete Department", False, "Admin token or department required")
            return False
            
        dept_id = self.created_departments[-1]  # Delete the last one
        
        success, response = self.make_request("DELETE", f"/ai/departments/{dept_id}", token=self.admin_token)
        
        if success and response.get("ok"):
            self.created_departments.remove(dept_id)
            self.log_result("Delete Department", True, f"Department deleted: {dept_id}")
            return True
        else:
            self.log_result("Delete Department", False, f"Error: {response}")
            return False
            
    # ============================================
    # TESTES DE CONFIG
    # ============================================
    
    def test_get_config(self) -> bool:
        """Test 14: GET /api/config (obter configurações)"""
        if not self.admin_token:
            self.log_result("Get Config", False, "Admin token required")
            return False
            
        success, response = self.make_request("GET", "/config", token=self.admin_token)
        
        if success and isinstance(response, dict):
            # Check for required fields
            required_fields = ["quick_blocks", "auto_reply", "apps", "pix_key", "allowed_data", "api_integration", "ai_agent"]
            missing_fields = [field for field in required_fields if field not in response]
            
            if not missing_fields:
                self.log_result("Get Config", True, f"Config loaded with all required fields")
                return True
            else:
                self.log_result("Get Config", False, f"Missing fields: {missing_fields}")
                return False
        else:
            self.log_result("Get Config", False, f"Error: {response}")
            return False
    
    def test_update_config(self) -> bool:
        """Test 15: PUT /api/config (atualizar configurações)"""
        if not self.admin_token:
            self.log_result("Update Config", False, "Admin token required")
            return False
            
        config_data = {
            "quick_blocks": [{"name": "Teste", "text": "Mensagem de teste"}],
            "auto_reply": [{"q": "oi", "a": "Olá! Como posso ajudar?"}],
            "apps": [],
            "pix_key": "test-pix-key-123",
            "allowed_data": {
                "cpfs": ["123.456.789-00"],
                "emails": ["test@example.com"],
                "phones": ["11999999999"],
                "random_keys": ["test-key-123"]
            },
            "api_integration": {
                "api_url": "https://api.test.com",
                "api_token": "test-token",
                "api_enabled": True
            },
            "ai_agent": {
                "name": "Assistente IA Teste",
                "personality": "Amigável e prestativo",
                "instructions": "Sempre seja educado",
                "llm_provider": "openai",
                "llm_model": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 500,
                "mode": "standby",
                "active_hours": "24/7",
                "enabled": True,
                "can_access_credentials": True,
                "knowledge_base": "Base de conhecimento teste"
            }
        }
        
        success, response = self.make_request("PUT", "/config", config_data, self.admin_token)
        
        if success and response.get("ok"):
            self.log_result("Update Config", True, "Config updated successfully")
            return True
        else:
            self.log_result("Update Config", False, f"Error: {response}")
            return False
            
    # ============================================
    # TESTES DE REVENDAS
    # ============================================
    
    def test_list_resellers(self) -> bool:
        """Test 16: GET /api/resellers (listar)"""
        if not self.admin_token:
            self.log_result("List Resellers", False, "Admin token required")
            return False
            
        success, response = self.make_request("GET", "/resellers", token=self.admin_token)
        
        if success and isinstance(response, list):
            count = len(response)
            self.log_result("List Resellers", True, f"Found {count} resellers")
            return True
        else:
            self.log_result("List Resellers", False, f"Error: {response}")
            return False
    
    def test_create_reseller(self) -> bool:
        """Test 17: POST /api/resellers (criar)"""
        if not self.admin_token:
            self.log_result("Create Reseller", False, "Admin token required")
            return False
            
        reseller_data = {
            "name": "Revenda Teste Backend",
            "email": "teste@backend.com",
            "password": "senha123",
            "domain": "teste.backend.com",
            "parent_id": None
        }
        
        success, response = self.make_request("POST", "/resellers", reseller_data, self.admin_token)
        
        if success and response.get("ok"):
            reseller_id = response.get("reseller_id")
            if reseller_id:
                self.created_resellers.append(reseller_id)
            self.log_result("Create Reseller", True, f"Reseller created with ID: {reseller_id}")
            return True
        else:
            self.log_result("Create Reseller", False, f"Error: {response}")
            return False
    
    def test_reseller_login(self) -> bool:
        """Test 18: Reseller Login (michaelrv@gmail.com / ab181818ab)"""
        login_data = {
            "email": "michaelrv@gmail.com",
            "password": "ab181818ab"
        }
        
        success, response = self.make_request("POST", "/resellers/login", login_data)
        
        if success and "token" in response:
            self.reseller_token = response["token"]
            reseller_id = response.get("reseller_id")
            self.log_result("Reseller Login (ajuda.vip)", True, f"Reseller logged in: {reseller_id}")
            return True
        else:
            self.log_result("Reseller Login (ajuda.vip)", False, f"Error: {response}")
            return False
            
    def test_delete_with_children_blocked(self) -> bool:
        """Test 7: Try Delete Reseller with Children (Should Block)"""
        if len(self.created_resellers) < 2:
            self.log_result("Delete with Children Blocked", False, "Need parent-child relationship")
            return False
            
        parent_id = self.created_resellers[0]  # Has children
        success, response = self.make_request("DELETE", f"/resellers/{parent_id}", 
                                            token=self.admin_token)
        
        # Should fail because it has children
        if not success and "sub-revenda" in str(response).lower():
            self.log_result("Delete with Children Blocked", True, "Correctly blocked deletion")
            return True
        else:
            self.log_result("Delete with Children Blocked", False, f"Should have been blocked: {response}")
            return False
            
    def test_reseller_login(self) -> bool:
        """Test 8: Reseller Login"""
        login_data = {
            "email": "raiz@teste.com",
            "password": "senha123"
        }
        
        success, response = self.make_request("POST", "/resellers/login", login_data)
        
        if success and "token" in response:
            reseller_id = response.get("reseller_id")
            self.reseller_tokens[reseller_id] = response["token"]
            self.log_result("Reseller Login", True, f"Reseller ID in token: {reseller_id}")
            return True
        else:
            self.log_result("Reseller Login", False, f"Error: {response}")
            return False
            
    def test_transfer_reseller(self) -> bool:
        """Test 9: Transfer Reseller to New Parent (Admin Only)"""
        if len(self.created_resellers) < 2:
            self.log_result("Transfer Reseller", False, "Need multiple resellers")
            return False
            
        transfer_data = {
            "reseller_id": self.created_resellers[1],  # Sub-reseller
            "new_parent_id": None  # Make it root
        }
        
        success, response = self.make_request("POST", "/resellers/transfer", 
                                            transfer_data, self.admin_token)
        
        if success and response.get("ok"):
            self.log_result("Transfer Reseller", True, "Transfer completed successfully")
            return True
        else:
            self.log_result("Transfer Reseller", False, f"Error: {response}")
            return False
            
    def test_data_isolation_agents(self) -> bool:
        """Test 10: Data Isolation - Agents"""
        # Create agent without reseller_id (should be master)
        agent_data = {
            "name": "Agente Master",
            "login": "agent_master",
            "password": "senha123",
            "avatar": ""
        }
        
        success, response = self.make_request("POST", "/agents", agent_data, self.admin_token)
        
        if not success or not response.get("ok"):
            self.log_result("Data Isolation - Agents", False, f"Failed to create master agent: {response}")
            return False
            
        # Now test with reseller token
        if not self.reseller_tokens:
            self.log_result("Data Isolation - Agents", False, "No reseller token available")
            return False
            
        reseller_token = list(self.reseller_tokens.values())[0]
        
        # Create agent as reseller (should have reseller_id)
        agent_data_reseller = {
            "name": "Agente Revenda",
            "login": "agent_reseller",
            "password": "senha123",
            "avatar": ""
        }
        
        success, response = self.make_request("POST", "/agents", agent_data_reseller, reseller_token)
        
        if success and response.get("ok"):
            self.log_result("Data Isolation - Agents", True, "Agents created with proper isolation")
            return True
        else:
            self.log_result("Data Isolation - Agents", False, f"Failed to create reseller agent: {response}")
            return False
            
    def test_list_agents_isolation(self) -> bool:
        """Test 11: List Agents with Tenant Isolation"""
        # List as admin (should see all)
        success_admin, response_admin = self.make_request("GET", "/agents", token=self.admin_token)
        
        if not success_admin:
            self.log_result("List Agents Isolation", False, f"Admin list failed: {response_admin}")
            return False
            
        admin_count = len(response_admin) if isinstance(response_admin, list) else 0
        
        # List as reseller (should see only their agents)
        if not self.reseller_tokens:
            self.log_result("List Agents Isolation", False, "No reseller token available")
            return False
            
        reseller_token = list(self.reseller_tokens.values())[0]
        success_reseller, response_reseller = self.make_request("GET", "/agents", token=reseller_token)
        
        if not success_reseller:
            self.log_result("List Agents Isolation", False, f"Reseller list failed: {response_reseller}")
            return False
            
        reseller_count = len(response_reseller) if isinstance(response_reseller, list) else 0
        
        # Admin should see more or equal agents than reseller
        if admin_count >= reseller_count:
            self.log_result("List Agents Isolation", True, 
                          f"Admin sees {admin_count}, Reseller sees {reseller_count}")
            return True
        else:
            self.log_result("List Agents Isolation", False, 
                          f"Isolation failed - Admin: {admin_count}, Reseller: {reseller_count}")
            return False
            
    def test_config_per_tenant(self) -> bool:
        """Test 12: Config per Tenant"""
        # Get config as admin
        success_admin, config_admin = self.make_request("GET", "/config", token=self.admin_token)
        
        if not success_admin:
            self.log_result("Config per Tenant", False, f"Admin config failed: {config_admin}")
            return False
            
        # Get config as reseller
        if not self.reseller_tokens:
            self.log_result("Config per Tenant", False, "No reseller token available")
            return False
            
        reseller_token = list(self.reseller_tokens.values())[0]
        success_reseller, config_reseller = self.make_request("GET", "/config", token=reseller_token)
        
        if not success_reseller:
            self.log_result("Config per Tenant", False, f"Reseller config failed: {config_reseller}")
            return False
            
        # Check if configs have proper structure
        admin_has_id = "id" in config_admin
        reseller_has_reseller_id = "reseller_id" in config_reseller
        
        if admin_has_id and reseller_has_reseller_id:
            self.log_result("Config per Tenant", True, "Configs properly isolated")
            return True
        else:
            self.log_result("Config per Tenant", False, 
                          f"Config structure issue - Admin: {admin_has_id}, Reseller: {reseller_has_reseller_id}")
            return False
            
    def test_update_reseller_config(self) -> bool:
        """Test 13: Update Reseller Config"""
        if not self.reseller_tokens:
            self.log_result("Update Reseller Config", False, "No reseller token available")
            return False
            
        reseller_token = list(self.reseller_tokens.values())[0]
        
        config_data = {
            "quick_blocks": [{"name": "Teste", "text": "Mensagem de teste"}],
            "auto_reply": [{"q": "oi", "a": "Olá! Como posso ajudar?"}],
            "apps": []
        }
        
        success, response = self.make_request("PUT", "/config", config_data, reseller_token)
        
        if success and response.get("ok"):
            self.log_result("Update Reseller Config", True, "Config updated successfully")
            return True
        else:
            self.log_result("Update Reseller Config", False, f"Error: {response}")
            return False
            
    def test_replicate_config(self) -> bool:
        """Test 14: Replicate Config to All Resellers (Admin Only)"""
        success, response = self.make_request("POST", "/resellers/replicate-config", 
                                            token=self.admin_token)
        
        if success and response.get("ok"):
            updated_count = response.get("updated", 0)
            self.log_result("Replicate Config", True, f"Replicated to {updated_count} resellers")
            return True
        else:
            self.log_result("Replicate Config", False, f"Error: {response}")
            return False
            
    def cleanup(self):
        """Clean up created test data"""
        print("\n🧹 Cleaning up test data...")
        
        # Delete created resellers (in reverse order to handle hierarchy)
        for reseller_id in reversed(self.created_resellers):
            success, response = self.make_request("DELETE", f"/resellers/{reseller_id}", 
                                                token=self.admin_token)
            if success:
                print(f"✅ Deleted reseller: {reseller_id}")
            else:
                print(f"❌ Failed to delete reseller {reseller_id}: {response}")
                
    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting Multi-Tenant System Tests")
        print("=" * 50)
        
        tests = [
            self.test_admin_login,
            self.test_create_root_reseller,
            self.test_create_sub_reseller,
            self.test_list_resellers,
            self.test_hierarchy_view,
            self.test_update_custom_domain,
            self.test_delete_with_children_blocked,
            self.test_reseller_login,
            self.test_transfer_reseller,
            self.test_data_isolation_agents,
            self.test_list_agents_isolation,
            self.test_config_per_tenant,
            self.test_update_reseller_config,
            self.test_replicate_config
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
            print("🎉 All tests passed! Multi-tenant system is working correctly.")
        else:
            print(f"⚠️  {total - passed} tests failed. Check the issues above.")
            
        # Cleanup
        if self.created_resellers:
            self.cleanup()
            
        return passed, total, self.test_results

def main():
    """Main test execution"""
    print(f"🔗 Testing backend at: {API_BASE}")
    
    tester = MultiTenantTester()
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