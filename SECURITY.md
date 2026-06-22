# Guia de Segurança — Projeto Tesouro Direto ETL

## ⚠️ Dados Críticos — NUNCA faça commit sem remover

Este projeto contém **credenciais e configurações sensíveis** que devem ser **SEMPRE mantidas fora do controle de versão**.

---

## 📋 Checklist de Segurança Antes do Commit

- [ ] `.env_kafka_connect` preenchido com **placeholders**, não com chaves reais
- [ ] `spark/.env` preenchido com **placeholders**, não com chaves reais
- [ ] Variáveis de ambiente sensíveis **removidas** dos arquivos de configuração
- [ ] `.gitignore` contém `.env*` e exclui arquivos sensíveis
- [ ] Nenhum arquivo de log com credenciais foi commitado
- [ ] Nenhuma senha ou chave visível em notebooks/scripts públicos

---

## 🔐 Arquivos a Configurar Localmente

Você **DEVE** criar esses arquivos localmente com suas credenciais reais. **Eles NÃO devem ir para Git.**

### 1. `.env_kafka_connect` (credenciais AWS)
```bash
cp .env_kafka_connect.example .env_kafka_connect
```
Preencha com suas chaves AWS reais:
```
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
```

### 2. `spark/.env` (credenciais AWS para Spark)
```bash
# Use o .env.example como template
cp spark/.env.example spark/.env
```
Preencha com suas chaves AWS reais.

### 3. Credenciais Postgres (para conectores Kafka)
As credenciais Postgres nos arquivos de configuração devem ser **parametrizadas**.
Adicione ao seu `.env_kafka_connect`:
```
POSTGRES_USER=seu_usuario
POSTGRES_PASSWORD=sua_senha
```

Depois, injete via `envsubst` ao registrar conectores:
```bash
envsubst < connectors/source/connect_jdbc_postgres_ipca.config > /tmp/ipca.config
curl -X POST http://localhost:8083/connectors \
  -H "Content-Type: application/json" \
  --data @/tmp/ipca.config
```

---

## 🛡️ Rotinas de Segurança

### Após cada execução com credenciais reais:

1. **Revoke AWS keys imediatamente** (AWS IAM console)
2. **Crie novas chaves** para a próxima sessão
3. **Nunca reutilize as mesmas chaves** em ambientes diferentes

### Ferramentas para detectar vazamentos:

```bash
# Verificar se há credenciais em staging
git diff --cached | grep -i "AKIA\|aws_secret"

# Verificar histórico de commits
git log --all -p | grep -i "password\|secret\|token" | head -20

# Usar git-secrets (recomendado)
brew install git-secrets  # macOS
git secrets --install
git secrets --register-aws
```

---

## ✅ Conformidade Git

O `.gitignore` foi atualizado para excluir:
- `.env*` (todos os arquivos de ambiente)
- `.env.example` e `.env_kafka_connect.example` (templates OK para versionar)
- `*.pem`, `*.key` (chaves criptográficas)
- `data/*.csv` (dados sensíveis)

Verifique antes de fazer push:
```bash
git status
git check-ignore .env_kafka_connect  # Deve retornar true
git check-ignore .env_kafka_connect.example  # Deve retornar false
```

---

## 📚 Referências

- [AWS Best Practices for Secrets Management](https://docs.aws.amazon.com/secretsmanager/)
- [OWASP: Sensitive Data Exposure](https://owasp.org/www-project-top-ten/)
- [Git Secrets Detection](https://github.com/awslabs/git-secrets)
