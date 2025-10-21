"""
Serviço de IA para responder mensagens automaticamente
Suporta OpenAI, Anthropic Claude e Google Gemini via Emergent LLM Key
"""
import os
from typing import List, Dict, Optional
from emergentintegrations.llm.chat import LlmChat, UserMessage
import logging

logger = logging.getLogger(__name__)

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
        try:
            # Usar API key do agente ou fallback para Emergent key
            api_key = agent_config.get('api_key', self.api_key)
            if not api_key:
                logger.error("Nenhuma API key configurada para IA")
                return None
            
            # Construir system message com todas as instruções
            system_message = self._build_system_prompt(agent_config, client_data)
            
            # Configurar chat
            provider = agent_config.get('llm_provider', 'openai')
            model = agent_config.get('llm_model', 'gpt-4o-mini')
            
            chat = LlmChat(
                api_key=api_key,
                session_id=f"agent_{agent_config.get('id', 'default')}",
                system_message=system_message
            ).with_model(provider, model)
            
            # Criar mensagem do usuário
            user_message = UserMessage(text=message)
            
            # Enviar e obter resposta
            response = await chat.send_message(user_message)
            
            logger.info(f"IA respondeu para mensagem: {message[:50]}...")
            return response
            
        except Exception as e:
            logger.error(f"Erro ao gerar resposta da IA: {str(e)}")
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
