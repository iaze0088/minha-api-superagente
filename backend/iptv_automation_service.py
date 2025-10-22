"""
Serviço de Automação IPTV - Sistema Robusto e Inteligente
Suporta automação via Playwright com retry, validação e fallback manual
"""
import asyncio
import traceback
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from playwright.async_api import async_playwright, Page, Browser


class AutomationResult:
    """Resultado da automação"""
    def __init__(self):
        self.success = False
        self.message = ""
        self.final_url = ""
        self.screenshots = []  # Lista de screenshots em base64
        self.logs = []  # Lista de logs
        self.error = None
        self.automation_score = 0  # Score de automatizabilidade (0-100)
    
    def add_log(self, log: str, level: str = "info"):
        """Adiciona log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logs.append({
            "time": timestamp,
            "level": level,
            "message": log
        })
        print(f"[{timestamp}] [{level.upper()}] {log}")
    
    def to_dict(self):
        """Converte para dicionário"""
        return {
            "success": self.success,
            "message": self.message,
            "final_url": self.final_url,
            "screenshots": self.screenshots,
            "logs": self.logs,
            "error": self.error,
            "automation_score": self.automation_score
        }


class IPTVAutomationBase:
    """Classe base para automação de apps IPTV"""
    
    def __init__(self, app_data: Dict, form_data: Dict):
        self.app_data = app_data
        self.form_data = form_data
        self.result = AutomationResult()
        self.page: Optional[Page] = None
        self.browser: Optional[Browser] = None
    
    async def take_screenshot(self, description: str = ""):
        """Tira screenshot e adiciona ao resultado"""
        try:
            if self.page:
                screenshot = await self.page.screenshot(type='png', full_page=False)
                screenshot_base64 = screenshot.hex()
                self.result.screenshots.append({
                    "description": description,
                    "data": screenshot_base64[:1000]  # Limitar tamanho
                })
                self.result.add_log(f"📸 Screenshot capturado: {description}")
        except Exception as e:
            self.result.add_log(f"⚠️ Erro ao capturar screenshot: {e}", "warning")
    
    async def wait_and_retry(self, action, max_retries: int = 3, delay: int = 1000):
        """Executa ação com retry"""
        for attempt in range(max_retries):
            try:
                await action()
                return True
            except Exception as e:
                if attempt < max_retries - 1:
                    self.result.add_log(f"⚠️ Tentativa {attempt + 1}/{max_retries} falhou: {e}. Tentando novamente...", "warning")
                    await self.page.wait_for_timeout(delay)
                else:
                    self.result.add_log(f"❌ Todas as tentativas falharam: {e}", "error")
                    raise e
        return False
    
    async def try_multiple_selectors(self, selectors: List[str], action: str, value: str = None) -> bool:
        """Tenta múltiplos seletores até encontrar um que funcione"""
        for selector in selectors:
            try:
                if action == "fill":
                    await self.page.fill(selector, value, timeout=5000)
                    self.result.add_log(f"✅ Campo preenchido com sucesso: {selector}")
                    return True
                elif action == "click":
                    await self.page.click(selector, timeout=5000)
                    self.result.add_log(f"✅ Botão clicado com sucesso: {selector}")
                    return True
                elif action == "wait":
                    await self.page.wait_for_selector(selector, timeout=5000)
                    self.result.add_log(f"✅ Elemento encontrado: {selector}")
                    return True
            except Exception:
                continue
        
        self.result.add_log(f"⚠️ Nenhum seletor funcionou para ação '{action}'", "warning")
        return False
    
    async def generate_final_url(self) -> str:
        """Gera URL final com template"""
        url_template = self.app_data.get('url_template', '')
        final_url = url_template
        
        for field, value in self.form_data.items():
            final_url = final_url.replace(f'{{{field}}}', str(value))
        
        self.result.add_log(f"🔗 URL gerada: {final_url}")
        return final_url
    
    async def initialize_browser(self):
        """Inicializa o navegador Playwright"""
        async with async_playwright() as p:
            self.result.add_log("🚀 Iniciando navegador...")
            
            self.browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            
            context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            self.page = await context.new_page()
            self.result.add_log("✅ Navegador iniciado com sucesso!")
            
            # Executar automação específica
            await self.run_automation()
            
            await self.browser.close()
    
    async def run_automation(self):
        """Método abstrato - deve ser implementado por subclasses"""
        raise NotImplementedError("Subclasses devem implementar run_automation()")
    
    async def execute(self) -> AutomationResult:
        """Executa a automação completa"""
        try:
            await self.initialize_browser()
            self.result.success = True
            self.result.message = "Automação concluída com sucesso!"
        except Exception as e:
            self.result.success = False
            self.result.error = str(e)
            self.result.message = f"Erro na automação: {str(e)}"
            self.result.add_log(f"❌ ERRO CRÍTICO: {e}", "error")
            self.result.add_log(f"📋 Stack trace: {traceback.format_exc()}", "error")
        
        return self.result


class SSIPTVAutomation(IPTVAutomationBase):
    """Automação específica para SS-IPTV"""
    
    async def run_automation(self):
        """Executa automação do SS-IPTV"""
        self.result.add_log("🔧 Iniciando automação SS-IPTV...")
        
        # Navegar para o site
        config_url = self.app_data.get('config_url')
        self.result.add_log(f"📍 Navegando para {config_url}")
        
        await self.page.goto(config_url, wait_until='domcontentloaded', timeout=60000)
        await self.page.wait_for_timeout(3000)
        await self.take_screenshot("Página inicial carregada")
        
        # Preencher código
        codigo = self.form_data.get('codigo', '')
        if codigo:
            self.result.add_log(f"📝 Preenchendo código: {codigo}")
            
            code_selectors = [
                'input[name="code"]',
                'input#code',
                'input#activation_code',
                'input[placeholder*="code" i]',
                'input[type="text"]',
                'input.code'
            ]
            
            success = await self.try_multiple_selectors(code_selectors, "fill", codigo)
            if not success:
                raise Exception("Não foi possível preencher o código. Seletores não encontrados.")
            
            await self.page.wait_for_timeout(1000)
            await self.take_screenshot("Código preenchido")
        
        # Clicar no botão submit
        self.result.add_log("🔘 Procurando botão de submit...")
        
        submit_selectors = [
            'button[type="submit"]',
            'input[type="submit"]',
            'button:has-text("Submit")',
            'button:has-text("Go")',
            'button:has-text("Activate")',
            'button.submit',
            'button#submit'
        ]
        
        success = await self.try_multiple_selectors(submit_selectors, "click")
        if success:
            await self.page.wait_for_timeout(3000)
            await self.take_screenshot("Após submit")
        
        # Gerar URL final
        username = self.form_data.get('username', '')
        password = self.form_data.get('password', '')
        
        if username and password:
            self.result.final_url = await self.generate_final_url()
            
            # Tentar preencher URL no site
            self.result.add_log("📋 Tentando preencher URL no site...")
            
            url_selectors = [
                'input[name="url"]',
                'input#url',
                'textarea[name="playlist"]',
                'textarea',
                'input[type="url"]',
                'input[placeholder*="url" i]'
            ]
            
            await self.try_multiple_selectors(url_selectors, "fill", self.result.final_url)
            await self.take_screenshot("URL preenchida")
            
            # Verificar se precisa clicar em algum botão final
            final_submit_selectors = [
                'button:has-text("Save")',
                'button:has-text("Add")',
                'button:has-text("Submit")',
                'button[type="submit"]'
            ]
            
            if await self.try_multiple_selectors(final_submit_selectors, "click"):
                await self.page.wait_for_timeout(2000)
                await self.take_screenshot("Configuração finalizada")
        
        self.result.add_log("✅ Automação SS-IPTV concluída!")
        self.result.automation_score = 85


class SmartOneAutomation(IPTVAutomationBase):
    """Automação específica para SmartOne IPTV"""
    
    async def run_automation(self):
        """Executa automação do SmartOne"""
        self.result.add_log("🔧 Iniciando automação SmartOne...")
        
        # Navegar para o site
        config_url = self.app_data.get('config_url')
        self.result.add_log(f"📍 Navegando para {config_url}")
        
        await self.page.goto(config_url, wait_until='domcontentloaded', timeout=60000)
        await self.page.wait_for_timeout(3000)
        await self.take_screenshot("Página inicial carregada")
        
        # Preencher MAC
        mac = self.form_data.get('mac', '')
        if mac:
            self.result.add_log(f"📝 Preenchendo MAC: {mac}")
            
            mac_selectors = [
                'input[name="mac"]',
                'input#mac',
                'input[placeholder*="MAC" i]',
                'input[type="text"]'
            ]
            
            success = await self.try_multiple_selectors(mac_selectors, "fill", mac)
            if not success:
                raise Exception("Não foi possível preencher o MAC. Seletores não encontrados.")
            
            await self.page.wait_for_timeout(1000)
            await self.take_screenshot("MAC preenchido")
        
        # Preencher nome da pasta
        nome_pasta = self.form_data.get('nome_pasta', '')
        if nome_pasta:
            self.result.add_log(f"📝 Preenchendo nome da pasta: {nome_pasta}")
            
            nome_selectors = [
                'input[name="name"]',
                'input#name',
                'input[name="folder"]',
                'input[placeholder*="name" i]'
            ]
            
            await self.try_multiple_selectors(nome_selectors, "fill", nome_pasta)
            await self.take_screenshot("Nome preenchido")
        
        # Gerar e preencher URL
        self.result.final_url = await self.generate_final_url()
        
        self.result.add_log("📋 Tentando preencher URL no site...")
        
        url_selectors = [
            'input[name="url"]',
            'textarea',
            'input[type="url"]',
            'input.url',
            'input[placeholder*="url" i]'
        ]
        
        await self.try_multiple_selectors(url_selectors, "fill", self.result.final_url)
        await self.take_screenshot("URL preenchida")
        
        # Verificar botão de salvar
        save_selectors = [
            'button:has-text("Save")',
            'button:has-text("Add")',
            'button:has-text("Submit")',
            'button[type="submit"]'
        ]
        
        if await self.try_multiple_selectors(save_selectors, "click"):
            await self.page.wait_for_timeout(2000)
            await self.take_screenshot("Configuração finalizada")
        
        self.result.add_log("✅ Automação SmartOne concluída!")
        self.result.automation_score = 80


class IPTVAutomationFactory:
    """Factory para criar instâncias de automação"""
    
    @staticmethod
    def create(app_type: str, app_data: Dict, form_data: Dict) -> IPTVAutomationBase:
        """Cria instância de automação baseada no tipo de app"""
        automations = {
            "SSIPTV": SSIPTVAutomation,
            "SMARTONE": SmartOneAutomation,
            # Adicionar outros apps conforme implementados
        }
        
        automation_class = automations.get(app_type)
        
        if not automation_class:
            # Fallback para automação genérica
            raise NotImplementedError(f"Automação para {app_type} ainda não implementada")
        
        return automation_class(app_data, form_data)


# Função principal de automação
async def automate_iptv_app(app_data: Dict, form_data: Dict) -> Dict:
    """
    Automatiza configuração de app IPTV
    
    Args:
        app_data: Dados do app (type, config_url, url_template, etc)
        form_data: Dados do formulário (codigo, username, password, mac, etc)
    
    Returns:
        Dict com resultado da automação
    """
    try:
        app_type = app_data.get('type')
        
        # Criar instância de automação
        automation = IPTVAutomationFactory.create(app_type, app_data, form_data)
        
        # Executar automação
        result = await automation.execute()
        
        return result.to_dict()
        
    except NotImplementedError as e:
        # App não tem automação implementada - retornar fallback para manual
        return {
            "success": False,
            "message": f"Automação para este app ainda não está disponível. Use o modo manual.",
            "error": str(e),
            "automation_score": 0,
            "logs": [{"time": datetime.now().strftime("%H:%M:%S"), "level": "info", "message": str(e)}],
            "screenshots": []
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Erro inesperado na automação: {str(e)}",
            "error": str(e),
            "automation_score": 0,
            "logs": [
                {"time": datetime.now().strftime("%H:%M:%S"), "level": "error", "message": str(e)},
                {"time": datetime.now().strftime("%H:%M:%S"), "level": "error", "message": traceback.format_exc()}
            ],
            "screenshots": []
        }
