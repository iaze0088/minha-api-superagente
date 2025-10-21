"""
Serviço de IA para responder mensagens automaticamente
Suporta OpenAI, Anthropic Claude e Google Gemini via Emergent LLM Key
"""
import os
from typing import List, Dict, Optional
from emergentintegrations.llm.chat import LlmChat, UserMessage
import logging
from datetime import datetime

# Configurar logger específico para IA com arquivo dedicado
logger = logging.getLogger("ai_agent")
logger.setLevel(logging.INFO)

# Handler para arquivo
file_handler = logging.FileHandler("/var/log/ai_agent.log")
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Handler para console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

class AIAgentService:
    """Serviço para gerenciar respostas de IA"""
    
    def __init__(self):
        self.api_key = os.getenv('EMERGENT_LLM_KEY', '')
    
    async def generate_response(
        self,
        agent_config: Dict,
        message: str,
        conversation_history: List[Dict] = None,
        client_data: Dict = None
    ) -> Optional[str]:
        """
        Gera resposta da IA baseada nas configurações do agente
        
        Args:
            agent_config: Configuração do agente IA (instruções, modelo, etc)
            message: Mensagem do cliente
            conversation_history: Histórico de mensagens (opcional)
            client_data: Dados do cliente (credenciais se permitido)
        
        Returns:
            Resposta da IA ou None se houver erro
        """
        logger.info("="*80)
        logger.info(f"🤖 INICIANDO GERAÇÃO DE RESPOSTA DA IA")
        logger.info(f"📝 Mensagem recebida: {message[:100]}...")
        logger.info(f"👤 Agente IA: {agent_config.get('name', 'Sem nome')} (ID: {agent_config.get('id', 'N/A')})")
        
        try:
            # Usar API key do agente ou fallback para Emergent key
            api_key = agent_config.get('api_key', self.api_key)
            if not api_key:
                logger.error("💥 ERRO CRÍTICO: Nenhuma API key configurada para IA")
                return None
            
            logger.info(f"🔑 API Key presente: {api_key[:10]}...{api_key[-4:] if len(api_key) > 14 else ''}")
            
            # Construir system message com todas as instruções
            system_message = self._build_system_prompt(agent_config, client_data)
            logger.info(f"📋 System Prompt construído ({len(system_message)} caracteres)")
            logger.info(f"📋 System Prompt preview: {system_message[:200]}...")
            
            # Configurar chat
            provider = agent_config.get('llm_provider', 'openai')
            model = agent_config.get('llm_model', 'gpt-4o-mini')
            
            logger.info(f"🔧 Configuração LLM:")
            logger.info(f"   - Provider: {provider}")
            logger.info(f"   - Model: {model}")
            logger.info(f"   - Session ID: agent_{agent_config.get('id', 'default')}")
            
            chat = LlmChat(
                api_key=api_key,
                session_id=f"agent_{agent_config.get('id', 'default')}",
                system_message=system_message
            ).with_model(provider, model)
            
            logger.info(f"✅ LlmChat configurado com sucesso")
            
            # Criar mensagem do usuário
            user_message = UserMessage(text=message)
            logger.info(f"📨 Enviando mensagem para LLM...")
            
            # Enviar e obter resposta
            response = await chat.send_message(user_message)
            
            logger.info(f"✅ RESPOSTA RECEBIDA DO LLM!")
            logger.info(f"📤 Resposta ({len(response)} caracteres): {response[:200]}...")
            logger.info("="*80)
            
            return response
            
        except Exception as e:
            logger.error(f"💥 ERRO CRÍTICO ao gerar resposta da IA:")
            logger.error(f"   Tipo: {type(e).__name__}")
            logger.error(f"   Mensagem: {str(e)}")
            import traceback
            logger.error(f"   Traceback:\n{traceback.format_exc()}")
            logger.info("="*80)
            return None
    
    def _build_system_prompt(self, agent_config: Dict, client_data: Dict = None) -> str:
        """Constrói o prompt do sistema com todas as configurações"""
        parts = []
        
        # Quem é o agente
        if agent_config.get('who_is'):
            parts.append(f"QUEM VOCÊ É: {agent_config['who_is']}")
        
        # O que faz
        if agent_config.get('what_does'):
            parts.append(f"O QUE VOCÊ FAZ: {agent_config['what_does']}")
        
        # Objetivo
        if agent_config.get('objective'):
            parts.append(f"SEU OBJETIVO: {agent_config['objective']}")
        
        # Como responder
        if agent_config.get('how_respond'):
            parts.append(f"COMO RESPONDER: {agent_config['how_respond']}")
        
        # Instruções gerais
        if agent_config.get('instructions'):
            parts.append(f"INSTRUÇÕES: {agent_config['instructions']}")
        
        # Base de conhecimento
        if agent_config.get('knowledge_base'):
            parts.append(f"BASE DE CONHECIMENTO:\n{agent_config['knowledge_base']}")
        
        # Temas a evitar
        if agent_config.get('avoid_topics'):
            parts.append(f"EVITE FALAR SOBRE: {agent_config['avoid_topics']}")
        
        # Palavras a evitar
        if agent_config.get('avoid_words'):
            parts.append(f"NÃO USE ESTAS PALAVRAS: {agent_config['avoid_words']}")
        
        # Links permitidos
        if agent_config.get('allowed_links'):
            parts.append(f"LINKS QUE VOCÊ PODE COMPARTILHAR:\n{agent_config['allowed_links']}")
        
        # Regras customizadas
        if agent_config.get('custom_rules'):
            parts.append(f"REGRAS ESPECIAIS:\n{agent_config['custom_rules']}")
        
        # Credenciais do cliente (se permitido)
        if agent_config.get('can_access_credentials') and client_data:
            if client_data.get('pinned_user') or client_data.get('pinned_pass'):
                parts.append(f"\nCREDENCIAIS DO CLIENTE (use quando necessário):")
                if client_data.get('pinned_user'):
                    parts.append(f"- Usuário: {client_data['pinned_user']}")
                if client_data.get('pinned_pass'):
                    parts.append(f"- Senha: {client_data['pinned_pass']}")
        
        # Restrição de conhecimento
        if agent_config.get('knowledge_restriction'):
            parts.append("\n⚠️ IMPORTANTE: Você só deve responder com base nas informações fornecidas acima. Se não souber algo, diga que não tem essa informação.")
        
        # Detector de idioma
        if agent_config.get('auto_detect_language'):
            parts.append("\n🌍 Detecte o idioma do usuário e responda no mesmo idioma automaticamente.")
        
        # Timezone
        timezone = agent_config.get('timezone', 'America/Sao_Paulo')
        parts.append(f"\n🕐 Fuso horário: {timezone}")
        
        return "\n\n".join(parts)

# Instância global
ai_service = AIAgentService()
