#!/usr/bin/env python3
"""
🔒 TESTE EXAUSTIVO DE ISOLAMENTO MULTI-TENANT - AUDITORIA DE SEGURANÇA

CONTEXTO:
Foi aplicada auditoria completa de segurança multi-tenant com função get_tenant_filter centralizada em 20+ endpoints críticos.
Um bug crítico foi identificado onde agente de revenda conseguia visualizar tickets do Admin Principal.

OBJETIVO:
Validar que o isolamento multi-tenant está 100% funcional após as correções aplicadas.

CENÁRIOS CRÍTICOS A TESTAR:
1. ISOLAMENTO DE TICKETS
2. ISOLAMENTO DE AGENTS  
3. ISOLAMENTO DE AI AGENTS
4. ISOLAMENTO DE DEPARTMENTS
5. ISOLAMENTO DE IPTV APPS
6. ISOLAMENTO DE NOTICES
7. ISOLAMENTO DE AUTO-RESPONDERS E TUTORIALS

CREDENCIAIS:
- Admin Master: senha do .env (102030@ab)
- Criar 2 resellers (A e B) com credenciais de teste
- Criar 1 agent para cada reseller

VALIDAÇÕES:
✅ Nenhum agent deve conseguir ver dados de outra revenda
✅ Nenhum agent deve conseguir ver dados do Admin Principal
✅ Resellers devem ver apenas seus próprios dados
✅ Admin Master deve ver TUDO sem filtros
"""

import requests
import json
import os
from typing import Dict, Optional, List
import time
import uuid

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://iptv-support-hub.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
ADMIN_PASSWORD = "102030@ab"  # From .env file

class MultiTenantSecurityTester:
    def __init__(self):
        self.admin_token = None
        self.reseller_a_token = None
        self.reseller_b_token = None
        self.agent_a_token = None
        self.agent_b_token = None
        
        # IDs for cleanup
        self.created_resellers = []
        self.created_agents = []
        self.created_ai_agents = []
        self.created_departments = []
        self.created_tickets = []
        self.created_notices = []
        self.created_iptv_apps = []
        self.created_auto_responders = []
        self.created_tutorials = []
        
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
    # SETUP - CRIAR ESTRUTURA DE TESTE
    # ============================================
    
    def setup_admin_login(self) -> bool:
        """Setup: Admin Master Login"""
        success, response = self.make_request("POST", "/auth/admin/login", {
            "password": ADMIN_PASSWORD
        })
        
        if success and "token" in response:
            self.admin_token = response["token"]
            self.log_result("Setup Admin Login", True, "Admin Master authenticated")
            return True
        else:
            self.log_result("Setup Admin Login", False, f"Error: {response}")
            return False
    
    def setup_create_resellers(self) -> bool:
        """Setup: Criar Reseller A e Reseller B"""
        if not self.admin_token:
            self.log_result("Setup Create Resellers", False, "Admin token required")
            return False
        
        # Criar Reseller A
        reseller_a_data = {
            "name": "Reseller A - Security Test",
            "email": "reseller_a@security.test",
            "password": "senha123",
            "domain": "reseller-a.test.com",
            "parent_id": None
        }
        
        success, response = self.make_request("POST", "/resellers", reseller_a_data, self.admin_token)
        if not success:
            self.log_result("Setup Create Resellers", False, f"Failed to create Reseller A: {response}")
            return False
        
        reseller_a_id = response.get("reseller_id")
        self.created_resellers.append(reseller_a_id)
        
        # Login Reseller A
        login_a_data = {
            "email": "reseller_a@security.test",
            "password": "senha123"
        }
        
        success, response = self.make_request("POST", "/resellers/login", login_a_data)
        if not success:
            self.log_result("Setup Create Resellers", False, f"Failed to login Reseller A: {response}")
            return False
        
        self.reseller_a_token = response["token"]
        
        # Criar Reseller B
        reseller_b_data = {
            "name": "Reseller B - Security Test",
            "email": "reseller_b@security.test",
            "password": "senha456",
            "domain": "reseller-b.test.com",
            "parent_id": None
        }
        
        success, response = self.make_request("POST", "/resellers", reseller_b_data, self.admin_token)
        if not success:
            self.log_result("Setup Create Resellers", False, f"Failed to create Reseller B: {response}")
            return False
        
        reseller_b_id = response.get("reseller_id")
        self.created_resellers.append(reseller_b_id)
        
        # Login Reseller B
        login_b_data = {
            "email": "reseller_b@security.test",
            "password": "senha456"
        }
        
        success, response = self.make_request("POST", "/resellers/login", login_b_data)
        if not success:
            self.log_result("Setup Create Resellers", False, f"Failed to login Reseller B: {response}")
            return False
        
        self.reseller_b_token = response["token"]
        
        self.log_result("Setup Create Resellers", True, f"Reseller A: {reseller_a_id}, Reseller B: {reseller_b_id}")
        return True
    
    def setup_create_agents(self) -> bool:
        """Setup: Criar Agent A (da Reseller A) e Agent B (da Reseller B)"""
        if not self.reseller_a_token or not self.reseller_b_token:
            self.log_result("Setup Create Agents", False, "Reseller tokens required")
            return False
        
        # Criar Agent A (usando token da Reseller A)
        agent_a_data = {
            "name": "Agent A - Security Test",
            "login": "agent_a_security",
            "password": "senha123",
            "avatar": ""
        }
        
        success, response = self.make_request("POST", "/agents", agent_a_data, self.reseller_a_token)
        if not success:
            self.log_result("Setup Create Agents", False, f"Failed to create Agent A: {response}")
            return False
        
        agent_a_id = response.get("id")
        self.created_agents.append(agent_a_id)
        
        # Login Agent A
        login_a_data = {
            "login": "agent_a_security",
            "password": "senha123"
        }
        
        success, response = self.make_request("POST", "/auth/agent/login", login_a_data)
        if not success:
            self.log_result("Setup Create Agents", False, f"Failed to login Agent A: {response}")
            return False
        
        self.agent_a_token = response["token"]
        
        # Criar Agent B (usando token da Reseller B)
        agent_b_data = {
            "name": "Agent B - Security Test",
            "login": "agent_b_security",
            "password": "senha456",
            "avatar": ""
        }
        
        success, response = self.make_request("POST", "/agents", agent_b_data, self.reseller_b_token)
        if not success:
            self.log_result("Setup Create Agents", False, f"Failed to create Agent B: {response}")
            return False
        
        agent_b_id = response.get("id")
        self.created_agents.append(agent_b_id)
        
        # Login Agent B
        login_b_data = {
            "login": "agent_b_security",
            "password": "senha456"
        }
        
        success, response = self.make_request("POST", "/auth/agent/login", login_b_data)
        if not success:
            self.log_result("Setup Create Agents", False, f"Failed to login Agent B: {response}")
            return False
        
        self.agent_b_token = response["token"]
        
        self.log_result("Setup Create Agents", True, f"Agent A: {agent_a_id}, Agent B: {agent_b_id}")
        return True
    
    def setup_create_test_data(self) -> bool:
        """Setup: Criar dados de teste para cada tenant"""
        if not all([self.admin_token, self.reseller_a_token, self.reseller_b_token]):
            self.log_result("Setup Create Test Data", False, "All tokens required")
            return False
        
        # Criar tickets do Admin Master
        admin_ticket_data = {
            "from_type": "client",
            "from_id": str(uuid.uuid4()),
            "to_type": "agent",
            "to_id": "system",
            "kind": "text",
            "text": "Ticket do Admin Master"
        }
        
        # Criar AI Agents para cada tenant
        # Admin Master AI Agent
        admin_ai_data = {
            "name": "Admin Master AI Agent",
            "description": "AI Agent do Admin Master",
            "llm_provider": "openai",
            "llm_model": "gpt-4o-mini"
        }
        
        success, response = self.make_request("POST", "/ai/agents", admin_ai_data, self.admin_token)
        if success:
            self.created_ai_agents.append(response.get("id"))
        
        # Reseller A AI Agent
        reseller_a_ai_data = {
            "name": "Reseller A AI Agent",
            "description": "AI Agent da Reseller A",
            "llm_provider": "openai",
            "llm_model": "gpt-4o-mini"
        }
        
        success, response = self.make_request("POST", "/ai/agents", reseller_a_ai_data, self.reseller_a_token)
        if success:
            self.created_ai_agents.append(response.get("id"))
        
        # Reseller B AI Agent
        reseller_b_ai_data = {
            "name": "Reseller B AI Agent",
            "description": "AI Agent da Reseller B",
            "llm_provider": "openai",
            "llm_model": "gpt-4o-mini"
        }
        
        success, response = self.make_request("POST", "/ai/agents", reseller_b_ai_data, self.reseller_b_token)
        if success:
            self.created_ai_agents.append(response.get("id"))
        
        # Criar Departments para cada tenant
        # Admin Master Department
        admin_dept_data = {
            "name": "Admin Master Department",
            "description": "Department do Admin Master",
            "is_default": True,
            "timeout_seconds": 120
        }
        
        success, response = self.make_request("POST", "/ai/departments", admin_dept_data, self.admin_token)
        if success:
            self.created_departments.append(response.get("id"))
        
        # Reseller A Department
        reseller_a_dept_data = {
            "name": "Reseller A Department",
            "description": "Department da Reseller A",
            "is_default": True,
            "timeout_seconds": 120
        }
        
        success, response = self.make_request("POST", "/ai/departments", reseller_a_dept_data, self.reseller_a_token)
        if success:
            self.created_departments.append(response.get("id"))
        
        # Reseller B Department
        reseller_b_dept_data = {
            "name": "Reseller B Department",
            "description": "Department da Reseller B",
            "is_default": True,
            "timeout_seconds": 120
        }
        
        success, response = self.make_request("POST", "/ai/departments", reseller_b_dept_data, self.reseller_b_token)
        if success:
            self.created_departments.append(response.get("id"))
        
        # Criar IPTV Apps para cada tenant
        # Admin Master IPTV App
        admin_iptv_data = {
            "name": "Admin Master IPTV App",
            "category": "Smart TV",
            "provider": "Admin Provider",
            "instructions": "Instruções do Admin Master",
            "video_url": "https://admin.example.com/video",
            "is_active": True
        }
        
        success, response = self.make_request("POST", "/iptv-apps", admin_iptv_data, self.admin_token)
        if success:
            self.created_iptv_apps.append(response.get("id"))
        
        # Reseller A IPTV App
        reseller_a_iptv_data = {
            "name": "Reseller A IPTV App",
            "category": "Smart TV",
            "provider": "Reseller A Provider",
            "instructions": "Instruções da Reseller A",
            "video_url": "https://reseller-a.example.com/video",
            "is_active": True
        }
        
        success, response = self.make_request("POST", "/iptv-apps", reseller_a_iptv_data, self.reseller_a_token)
        if success:
            self.created_iptv_apps.append(response.get("id"))
        
        # Reseller B IPTV App
        reseller_b_iptv_data = {
            "name": "Reseller B IPTV App",
            "category": "Smart TV",
            "provider": "Reseller B Provider",
            "instructions": "Instruções da Reseller B",
            "video_url": "https://reseller-b.example.com/video",
            "is_active": True
        }
        
        success, response = self.make_request("POST", "/iptv-apps", reseller_b_iptv_data, self.reseller_b_token)
        if success:
            self.created_iptv_apps.append(response.get("id"))
        
        # Criar Notices para cada tenant
        # Admin Master Notice
        admin_notice_data = {
            "title": "Admin Master Notice",
            "content": "Aviso do Admin Master",
            "type": "info",
            "is_active": True
        }
        
        success, response = self.make_request("POST", "/notices", admin_notice_data, self.admin_token)
        if success:
            self.created_notices.append(response.get("id"))
        
        # Reseller A Notice
        reseller_a_notice_data = {
            "title": "Reseller A Notice",
            "content": "Aviso da Reseller A",
            "type": "info",
            "is_active": True
        }
        
        success, response = self.make_request("POST", "/notices", reseller_a_notice_data, self.reseller_a_token)
        if success:
            self.created_notices.append(response.get("id"))
        
        # Reseller B Notice
        reseller_b_notice_data = {
            "title": "Reseller B Notice",
            "content": "Aviso da Reseller B",
            "type": "info",
            "is_active": True
        }
        
        success, response = self.make_request("POST", "/notices", reseller_b_notice_data, self.reseller_b_token)
        if success:
            self.created_notices.append(response.get("id"))
        
        self.log_result("Setup Create Test Data", True, "Test data created for all tenants")
        return True

    # ============================================
    # TESTES DE ISOLAMENTO CRÍTICOS
    # ============================================
    
    def test_tickets_isolation(self) -> bool:
        """CRÍTICO: Isolamento de Tickets"""
        print("\n🎫 TESTANDO ISOLAMENTO DE TICKETS...")
        
        # Agent A deve ver APENAS tickets da Reseller A (NÃO ver tickets do admin ou reseller B)
        success, tickets_agent_a = self.make_request("GET", "/tickets", token=self.agent_a_token)
        if not success:
            self.log_result("Tickets Isolation - Agent A", False, f"Failed to get tickets: {tickets_agent_a}")
            return False
        
        # Verificar se Agent A não vê tickets do Admin ou Reseller B
        admin_tickets_visible = any("Admin Master" in str(ticket) for ticket in tickets_agent_a)
        reseller_b_tickets_visible = any("Reseller B" in str(ticket) for ticket in tickets_agent_a)
        
        if admin_tickets_visible or reseller_b_tickets_visible:
            self.log_result("Tickets Isolation - Agent A", False, f"Agent A can see admin/reseller B tickets! Admin: {admin_tickets_visible}, Reseller B: {reseller_b_tickets_visible}")
            return False
        
        # Agent B deve ver APENAS tickets da Reseller B (NÃO ver tickets do admin ou reseller A)
        success, tickets_agent_b = self.make_request("GET", "/tickets", token=self.agent_b_token)
        if not success:
            self.log_result("Tickets Isolation - Agent B", False, f"Failed to get tickets: {tickets_agent_b}")
            return False
        
        # Verificar se Agent B não vê tickets do Admin ou Reseller A
        admin_tickets_visible = any("Admin Master" in str(ticket) for ticket in tickets_agent_b)
        reseller_a_tickets_visible = any("Reseller A" in str(ticket) for ticket in tickets_agent_b)
        
        if admin_tickets_visible or reseller_a_tickets_visible:
            self.log_result("Tickets Isolation - Agent B", False, f"Agent B can see admin/reseller A tickets! Admin: {admin_tickets_visible}, Reseller A: {reseller_a_tickets_visible}")
            return False
        
        # Admin Master deve ver TODOS os tickets
        success, tickets_admin = self.make_request("GET", "/tickets", token=self.admin_token)
        if not success:
            self.log_result("Tickets Isolation - Admin", False, f"Failed to get admin tickets: {tickets_admin}")
            return False
        
        self.log_result("Tickets Isolation", True, f"Agent A: {len(tickets_agent_a)} tickets, Agent B: {len(tickets_agent_b)} tickets, Admin: {len(tickets_admin)} tickets")
        return True
    
    def test_agents_isolation(self) -> bool:
        """CRÍTICO: Isolamento de Agents"""
        print("\n👥 TESTANDO ISOLAMENTO DE AGENTS...")
        
        # Agent A deve ver APENAS agents da Reseller A
        success, agents_agent_a = self.make_request("GET", "/agents", token=self.agent_a_token)
        if not success:
            self.log_result("Agents Isolation - Agent A", False, f"Failed to get agents: {agents_agent_a}")
            return False
        
        # Verificar se Agent A não vê agents do Admin ou Reseller B
        admin_agents_visible = any("Admin Master" in agent.get("name", "") for agent in agents_agent_a)
        reseller_b_agents_visible = any("Agent B" in agent.get("name", "") for agent in agents_agent_a)
        
        if admin_agents_visible or reseller_b_agents_visible:
            self.log_result("Agents Isolation - Agent A", False, f"Agent A can see admin/reseller B agents! Admin: {admin_agents_visible}, Reseller B: {reseller_b_agents_visible}")
            return False
        
        # Agent B deve ver APENAS agents da Reseller B
        success, agents_agent_b = self.make_request("GET", "/agents", token=self.agent_b_token)
        if not success:
            self.log_result("Agents Isolation - Agent B", False, f"Failed to get agents: {agents_agent_b}")
            return False
        
        # Verificar se Agent B não vê agents do Admin ou Reseller A
        admin_agents_visible = any("Admin Master" in agent.get("name", "") for agent in agents_agent_b)
        reseller_a_agents_visible = any("Agent A" in agent.get("name", "") for agent in agents_agent_b)
        
        if admin_agents_visible or reseller_a_agents_visible:
            self.log_result("Agents Isolation - Agent B", False, f"Agent B can see admin/reseller A agents! Admin: {admin_agents_visible}, Reseller A: {reseller_a_agents_visible}")
            return False
        
        # Admin Master deve ver TODOS os agents
        success, agents_admin = self.make_request("GET", "/agents", token=self.admin_token)
        if not success:
            self.log_result("Agents Isolation - Admin", False, f"Failed to get admin agents: {agents_admin}")
            return False
        
        self.log_result("Agents Isolation", True, f"Agent A sees: {len(agents_agent_a)} agents, Agent B sees: {len(agents_agent_b)} agents, Admin sees: {len(agents_admin)} agents")
        return True
    
    def test_ai_agents_isolation(self) -> bool:
        """CRÍTICO: Isolamento de AI Agents"""
        print("\n🤖 TESTANDO ISOLAMENTO DE AI AGENTS...")
        
        # Reseller A deve ver APENAS IA agents da Reseller A
        success, ai_agents_reseller_a = self.make_request("GET", "/ai/agents", token=self.reseller_a_token)
        if not success:
            self.log_result("AI Agents Isolation - Reseller A", False, f"Failed to get AI agents: {ai_agents_reseller_a}")
            return False
        
        # Verificar se Reseller A não vê AI agents do Admin ou Reseller B
        admin_ai_visible = any("Admin Master" in agent.get("name", "") for agent in ai_agents_reseller_a)
        reseller_b_ai_visible = any("Reseller B" in agent.get("name", "") for agent in ai_agents_reseller_a)
        
        if admin_ai_visible or reseller_b_ai_visible:
            self.log_result("AI Agents Isolation - Reseller A", False, f"Reseller A can see admin/reseller B AI agents! Admin: {admin_ai_visible}, Reseller B: {reseller_b_ai_visible}")
            return False
        
        # Reseller B deve ver APENAS IA agents da Reseller B
        success, ai_agents_reseller_b = self.make_request("GET", "/ai/agents", token=self.reseller_b_token)
        if not success:
            self.log_result("AI Agents Isolation - Reseller B", False, f"Failed to get AI agents: {ai_agents_reseller_b}")
            return False
        
        # Verificar se Reseller B não vê AI agents do Admin ou Reseller A
        admin_ai_visible = any("Admin Master" in agent.get("name", "") for agent in ai_agents_reseller_b)
        reseller_a_ai_visible = any("Reseller A" in agent.get("name", "") for agent in ai_agents_reseller_b)
        
        if admin_ai_visible or reseller_a_ai_visible:
            self.log_result("AI Agents Isolation - Reseller B", False, f"Reseller B can see admin/reseller A AI agents! Admin: {admin_ai_visible}, Reseller A: {reseller_a_ai_visible}")
            return False
        
        # Admin Master deve ver TODOS os AI agents
        success, ai_agents_admin = self.make_request("GET", "/ai/agents", token=self.admin_token)
        if not success:
            self.log_result("AI Agents Isolation - Admin", False, f"Failed to get admin AI agents: {ai_agents_admin}")
            return False
        
        self.log_result("AI Agents Isolation", True, f"Reseller A sees: {len(ai_agents_reseller_a)} AI agents, Reseller B sees: {len(ai_agents_reseller_b)} AI agents, Admin sees: {len(ai_agents_admin)} AI agents")
        return True
    
    def test_departments_isolation(self) -> bool:
        """CRÍTICO: Isolamento de Departments"""
        print("\n🏢 TESTANDO ISOLAMENTO DE DEPARTMENTS...")
        
        # Reseller A deve ver APENAS departments da Reseller A
        success, departments_reseller_a = self.make_request("GET", "/ai/departments", token=self.reseller_a_token)
        if not success:
            self.log_result("Departments Isolation - Reseller A", False, f"Failed to get departments: {departments_reseller_a}")
            return False
        
        # Verificar se Reseller A não vê departments do Admin ou Reseller B
        admin_dept_visible = any("Admin Master" in dept.get("name", "") for dept in departments_reseller_a)
        reseller_b_dept_visible = any("Reseller B" in dept.get("name", "") for dept in departments_reseller_a)
        
        if admin_dept_visible or reseller_b_dept_visible:
            self.log_result("Departments Isolation - Reseller A", False, f"Reseller A can see admin/reseller B departments! Admin: {admin_dept_visible}, Reseller B: {reseller_b_dept_visible}")
            return False
        
        # Reseller B deve ver APENAS departments da Reseller B
        success, departments_reseller_b = self.make_request("GET", "/ai/departments", token=self.reseller_b_token)
        if not success:
            self.log_result("Departments Isolation - Reseller B", False, f"Failed to get departments: {departments_reseller_b}")
            return False
        
        # Verificar se Reseller B não vê departments do Admin ou Reseller A
        admin_dept_visible = any("Admin Master" in dept.get("name", "") for dept in departments_reseller_b)
        reseller_a_dept_visible = any("Reseller A" in dept.get("name", "") for dept in departments_reseller_b)
        
        if admin_dept_visible or reseller_a_dept_visible:
            self.log_result("Departments Isolation - Reseller B", False, f"Reseller B can see admin/reseller A departments! Admin: {admin_dept_visible}, Reseller A: {reseller_a_dept_visible}")
            return False
        
        # Admin Master deve ver TODOS os departments
        success, departments_admin = self.make_request("GET", "/ai/departments", token=self.admin_token)
        if not success:
            self.log_result("Departments Isolation - Admin", False, f"Failed to get admin departments: {departments_admin}")
            return False
        
        self.log_result("Departments Isolation", True, f"Reseller A sees: {len(departments_reseller_a)} departments, Reseller B sees: {len(departments_reseller_b)} departments, Admin sees: {len(departments_admin)} departments")
        return True
    
    def test_iptv_apps_isolation(self) -> bool:
        """CRÍTICO: Isolamento de IPTV Apps"""
        print("\n📺 TESTANDO ISOLAMENTO DE IPTV APPS...")
        
        # Reseller A deve ver APENAS apps da Reseller A
        success, apps_reseller_a = self.make_request("GET", "/iptv-apps", token=self.reseller_a_token)
        if not success:
            self.log_result("IPTV Apps Isolation - Reseller A", False, f"Failed to get IPTV apps: {apps_reseller_a}")
            return False
        
        # Verificar se Reseller A não vê apps do Admin ou Reseller B
        admin_app_visible = any("Admin Master" in app.get("name", "") for app in apps_reseller_a)
        reseller_b_app_visible = any("Reseller B" in app.get("name", "") for app in apps_reseller_a)
        
        if admin_app_visible or reseller_b_app_visible:
            self.log_result("IPTV Apps Isolation - Reseller A", False, f"Reseller A can see admin/reseller B apps! Admin: {admin_app_visible}, Reseller B: {reseller_b_app_visible}")
            return False
        
        # Reseller B deve ver APENAS apps da Reseller B
        success, apps_reseller_b = self.make_request("GET", "/iptv-apps", token=self.reseller_b_token)
        if not success:
            self.log_result("IPTV Apps Isolation - Reseller B", False, f"Failed to get IPTV apps: {apps_reseller_b}")
            return False
        
        # Verificar se Reseller B não vê apps do Admin ou Reseller A
        admin_app_visible = any("Admin Master" in app.get("name", "") for app in apps_reseller_b)
        reseller_a_app_visible = any("Reseller A" in app.get("name", "") for app in apps_reseller_b)
        
        if admin_app_visible or reseller_a_app_visible:
            self.log_result("IPTV Apps Isolation - Reseller B", False, f"Reseller B can see admin/reseller A apps! Admin: {admin_app_visible}, Reseller A: {reseller_a_app_visible}")
            return False
        
        # Admin Master deve ver TODOS os apps
        success, apps_admin = self.make_request("GET", "/iptv-apps", token=self.admin_token)
        if not success:
            self.log_result("IPTV Apps Isolation - Admin", False, f"Failed to get admin IPTV apps: {apps_admin}")
            return False
        
        self.log_result("IPTV Apps Isolation", True, f"Reseller A sees: {len(apps_reseller_a)} apps, Reseller B sees: {len(apps_reseller_b)} apps, Admin sees: {len(apps_admin)} apps")
        return True
    
    def test_notices_isolation(self) -> bool:
        """CRÍTICO: Isolamento de Notices"""
        print("\n📢 TESTANDO ISOLAMENTO DE NOTICES...")
        
        # Agent A deve ver APENAS notices da Reseller A
        success, notices_agent_a = self.make_request("GET", "/notices", token=self.agent_a_token)
        if not success:
            self.log_result("Notices Isolation - Agent A", False, f"Failed to get notices: {notices_agent_a}")
            return False
        
        # Verificar se Agent A não vê notices do Admin ou Reseller B
        admin_notice_visible = any("Admin Master" in notice.get("title", "") for notice in notices_agent_a)
        reseller_b_notice_visible = any("Reseller B" in notice.get("title", "") for notice in notices_agent_a)
        
        if admin_notice_visible or reseller_b_notice_visible:
            self.log_result("Notices Isolation - Agent A", False, f"Agent A can see admin/reseller B notices! Admin: {admin_notice_visible}, Reseller B: {reseller_b_notice_visible}")
            return False
        
        # Agent B deve ver APENAS notices da Reseller B
        success, notices_agent_b = self.make_request("GET", "/notices", token=self.agent_b_token)
        if not success:
            self.log_result("Notices Isolation - Agent B", False, f"Failed to get notices: {notices_agent_b}")
            return False
        
        # Verificar se Agent B não vê notices do Admin ou Reseller A
        admin_notice_visible = any("Admin Master" in notice.get("title", "") for notice in notices_agent_b)
        reseller_a_notice_visible = any("Reseller A" in notice.get("title", "") for notice in notices_agent_b)
        
        if admin_notice_visible or reseller_a_notice_visible:
            self.log_result("Notices Isolation - Agent B", False, f"Agent B can see admin/reseller A notices! Admin: {admin_notice_visible}, Reseller A: {reseller_a_notice_visible}")
            return False
        
        # Admin Master deve ver TODOS os notices
        success, notices_admin = self.make_request("GET", "/notices", token=self.admin_token)
        if not success:
            self.log_result("Notices Isolation - Admin", False, f"Failed to get admin notices: {notices_admin}")
            return False
        
        self.log_result("Notices Isolation", True, f"Agent A sees: {len(notices_agent_a)} notices, Agent B sees: {len(notices_agent_b)} notices, Admin sees: {len(notices_admin)} notices")
        return True
    
    def test_auto_responders_isolation(self) -> bool:
        """CRÍTICO: Isolamento de Auto-Responders"""
        print("\n🤖 TESTANDO ISOLAMENTO DE AUTO-RESPONDERS...")
        
        # Reseller A deve ver APENAS auto-responders da Reseller A
        success, auto_resp_reseller_a = self.make_request("GET", "/config/auto-responder-sequences", token=self.reseller_a_token)
        if not success:
            self.log_result("Auto-Responders Isolation - Reseller A", False, f"Failed to get auto-responders: {auto_resp_reseller_a}")
            return False
        
        # Reseller B deve ver APENAS auto-responders da Reseller B
        success, auto_resp_reseller_b = self.make_request("GET", "/config/auto-responder-sequences", token=self.reseller_b_token)
        if not success:
            self.log_result("Auto-Responders Isolation - Reseller B", False, f"Failed to get auto-responders: {auto_resp_reseller_b}")
            return False
        
        # Admin Master deve ver TODOS os auto-responders
        success, auto_resp_admin = self.make_request("GET", "/config/auto-responder-sequences", token=self.admin_token)
        if not success:
            self.log_result("Auto-Responders Isolation - Admin", False, f"Failed to get admin auto-responders: {auto_resp_admin}")
            return False
        
        self.log_result("Auto-Responders Isolation", True, f"Reseller A sees: {len(auto_resp_reseller_a)} sequences, Reseller B sees: {len(auto_resp_reseller_b)} sequences, Admin sees: {len(auto_resp_admin)} sequences")
        return True
    
    def test_tutorials_isolation(self) -> bool:
        """CRÍTICO: Isolamento de Tutorials"""
        print("\n📚 TESTANDO ISOLAMENTO DE TUTORIALS...")
        
        # Reseller A deve ver APENAS tutorials da Reseller A
        success, tutorials_reseller_a = self.make_request("GET", "/config/tutorials-advanced", token=self.reseller_a_token)
        if not success:
            self.log_result("Tutorials Isolation - Reseller A", False, f"Failed to get tutorials: {tutorials_reseller_a}")
            return False
        
        # Reseller B deve ver APENAS tutorials da Reseller B
        success, tutorials_reseller_b = self.make_request("GET", "/config/tutorials-advanced", token=self.reseller_b_token)
        if not success:
            self.log_result("Tutorials Isolation - Reseller B", False, f"Failed to get tutorials: {tutorials_reseller_b}")
            return False
        
        # Admin Master deve ver TODOS os tutorials
        success, tutorials_admin = self.make_request("GET", "/config/tutorials-advanced", token=self.admin_token)
        if not success:
            self.log_result("Tutorials Isolation - Admin", False, f"Failed to get admin tutorials: {tutorials_admin}")
            return False
        
        self.log_result("Tutorials Isolation", True, f"Reseller A sees: {len(tutorials_reseller_a)} tutorials, Reseller B sees: {len(tutorials_reseller_b)} tutorials, Admin sees: {len(tutorials_admin)} tutorials")
        return True

    # ============================================
    # CLEANUP
    # ============================================
    
    def cleanup(self):
        """Clean up created test data"""
        print("\n🧹 Cleaning up security test data...")
        
        if not self.admin_token:
            print("❌ No admin token for cleanup")
            return
        
        # Delete created resellers (this should cascade delete agents)
        for reseller_id in reversed(self.created_resellers):
            success, response = self.make_request("DELETE", f"/resellers/{reseller_id}", token=self.admin_token)
            if success:
                print(f"✅ Deleted reseller: {reseller_id}")
            else:
                print(f"❌ Failed to delete reseller {reseller_id}: {response}")
        
        # Delete created AI agents
        for ai_agent_id in self.created_ai_agents:
            success, response = self.make_request("DELETE", f"/ai/agents/{ai_agent_id}", token=self.admin_token)
            if success:
                print(f"✅ Deleted AI agent: {ai_agent_id}")
            else:
                print(f"❌ Failed to delete AI agent {ai_agent_id}: {response}")
        
        # Delete created departments
        for dept_id in self.created_departments:
            success, response = self.make_request("DELETE", f"/ai/departments/{dept_id}", token=self.admin_token)
            if success:
                print(f"✅ Deleted department: {dept_id}")
            else:
                print(f"❌ Failed to delete department {dept_id}: {response}")

    # ============================================
    # MAIN TEST RUNNER
    # ============================================
    
    def run_security_audit(self):
        """Run complete multi-tenant security audit"""
        print("🔒 TESTE EXAUSTIVO DE ISOLAMENTO MULTI-TENANT - AUDITORIA DE SEGURANÇA")
        print("=" * 80)
        
        # Setup phase
        setup_tests = [
            self.setup_admin_login,
            self.setup_create_resellers,
            self.setup_create_agents,
            self.setup_create_test_data,
        ]
        
        # Critical isolation tests
        isolation_tests = [
            self.test_tickets_isolation,
            self.test_agents_isolation,
            self.test_ai_agents_isolation,
            self.test_departments_isolation,
            self.test_iptv_apps_isolation,
            self.test_notices_isolation,
            self.test_auto_responders_isolation,
            self.test_tutorials_isolation,
        ]
        
        all_tests = setup_tests + isolation_tests
        
        passed = 0
        total = len(all_tests)
        failed_tests = []
        
        for test in all_tests:
            try:
                if test():
                    passed += 1
                else:
                    failed_tests.append(test.__name__)
                time.sleep(0.5)  # Small delay between tests
            except Exception as e:
                self.log_result(test.__name__, False, f"Exception: {str(e)}")
                failed_tests.append(test.__name__)
                
        print("\n" + "=" * 80)
        print(f"📊 RESULTADO FINAL DA AUDITORIA: {passed}/{total} testes passaram")
        
        if passed == total:
            print("🎉 ✅ AUDITORIA DE SEGURANÇA MULTI-TENANT PASSOU!")
            print("🔒 ISOLAMENTO 100% FUNCIONAL - Nenhum vazamento de dados detectado!")
        else:
            print(f"🚨 ❌ FALHAS DE SEGURANÇA DETECTADAS: {total - passed} testes falharam:")
            for failed_test in failed_tests:
                print(f"   ❌ {failed_test}")
            print("\n🚨 AÇÃO IMEDIATA NECESSÁRIA: Corrigir falhas de isolamento antes de produção!")
            
        # Cleanup
        if any([self.created_resellers, self.created_agents, self.created_ai_agents, 
                self.created_departments, self.created_iptv_apps, self.created_notices]):
            self.cleanup()
            
        return passed, total, self.test_results


if __name__ == "__main__":
    tester = MultiTenantSecurityTester()
    passed, total, results = tester.run_security_audit()
    
    # Exit with appropriate code
    exit(0 if passed == total else 1)