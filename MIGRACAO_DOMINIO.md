# 🚀 Migração do Domínio suporte.help

## ⚡ RESUMO RÁPIDO

**Situação atual:** suporte.help aponta para servidor antigo (PHP)
**Objetivo:** Migrar para o novo sistema (React + FastAPI)

---

## 📋 CHECKLIST DE MIGRAÇÃO

### ☑️ 1. Deploy na Emergent (OBRIGATÓRIO PRIMEIRO)
- [ ] Clicar em "Deploy" no painel Emergent
- [ ] Aguardar deployment finalizar (5-10 min)
- [ ] Verificar que está rodando

### ☑️ 2. Configurar Cloudflare DNS
- [ ] Acessar https://dash.cloudflare.com
- [ ] Ir em DNS → Records
- [ ] **Deletar** registro A antigo do suporte.help
- [ ] **Adicionar** novo registro:
  ```
  Tipo: A
  Nome: @
  IP: 34.57.15.54
  Proxy: DNS only (cinza)
  ```
- [ ] Salvar alterações

### ☑️ 3. Vincular Domínio na Emergent
- [ ] Ir em Deployments → Custom Domain
- [ ] Clicar "Link Domain"
- [ ] Digitar: suporte.help
- [ ] Aguardar verificação (5-15 min)

### ☑️ 4. Verificar Funcionamento
Execute no terminal:
```bash
/app/verificar_dominio.sh
```

---

## 🎯 URLs FINAIS

Após a migração:

- **Cliente:** https://suporte.help/
- **Atendente:** https://suporte.help/atendente/login
- **Admin:** https://suporte.help/admin/login

**Credenciais:**
- Admin: senha `102030@ab`
- Atendente: login `joao` / senha `123456`

---

## 🕐 TEMPO ESTIMADO

- Deploy na Emergent: 5-10 minutos
- Propagação DNS: 5-30 minutos
- Verificação domínio: 5-15 minutos

**Total: 15-55 minutos**

---

## ⚠️ IMPORTANTE

1. **NÃO delete o servidor antigo ainda!** Mantenha como backup
2. Teste tudo no domínio novo antes de desligar o antigo
3. Se algo der errado, basta voltar o DNS antigo

---

## 🆘 TROUBLESHOOTING

### "Domínio não resolve"
- Aguarde mais tempo (até 1 hora)
- Limpe cache DNS: `ipconfig /flushdns` (Windows) ou `sudo dscacheutil -flushcache` (Mac)

### "Certificado SSL inválido"
- Aguarde a Emergent configurar SSL automaticamente (pode levar até 24h)

### "Página não carrega"
- Verifique se deployment está ativo na Emergent
- Execute: `sudo supervisorctl status backend frontend`

### "API não funciona"
- Verifique `/app/backend/.env` contém:
  ```
  REACT_APP_BACKEND_URL="https://suporte.help"
  ```
- Reinicie: `sudo supervisorctl restart backend frontend`

---

## 📞 SUPORTE

Se precisar de ajuda:
1. Execute `/app/verificar_dominio.sh` e envie o resultado
2. Verifique logs: `tail -f /var/log/supervisor/backend.err.log`
3. Status: `sudo supervisorctl status`

---

## 🔄 ROLLBACK (Voltar ao antigo)

Se algo der errado, volte o DNS na Cloudflare:
1. Delete o registro A novo (34.57.15.54)
2. Adicione o registro A antigo
3. Aguarde propagação (5-30 min)
