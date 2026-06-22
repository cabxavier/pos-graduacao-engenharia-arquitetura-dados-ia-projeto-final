#!/usr/bin/env bash
# Script de validação de segurança antes do commit
# Use: bash scripts/pre-commit-security-check.sh

set -e

echo "🔒 Verificação de Segurança Pré-Commit"
echo "======================================="
echo

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

FAIL=0

# 1. Verificar se .env_kafka_connect contém credenciais reais
echo -n "✓ Verificando .env_kafka_connect... "
if grep -q "AKIA\|01NgAk" .env_kafka_connect 2>/dev/null; then
    echo -e "${RED}FALHA${NC} - Credenciais reais encontradas!"
    FAIL=1
else
    echo -e "${GREEN}OK${NC}"
fi

# 2. Verificar se spark/.env contém credenciais reais
echo -n "✓ Verificando spark/.env... "
if grep -q "AKIA\|01NgAk" spark/.env 2>/dev/null; then
    echo -e "${RED}FALHA${NC} - Credenciais reais encontradas!"
    FAIL=1
else
    echo -e "${GREEN}OK${NC}"
fi

# 3. Verificar se há arquivos .config (sem .example) em staging
echo -n "✓ Verificando connectors/*.config... "
if git diff --cached --name-only 2>/dev/null | grep -E "connectors/.*\.config$" | grep -v ".example"; then
    echo -e "${RED}FALHA${NC} - Arquivos .config em staging (devem estar em .gitignore)!"
    FAIL=1
else
    echo -e "${GREEN}OK${NC}"
fi

# 4. Verificar em todos os arquivos staged por padrões de credenciais
echo -n "✓ Verificando padrões de credenciais em staging... "
if git diff --cached | grep -iE "(password|secret|api[_-]?key|access[_-]?key|akia)" | grep -v "example\|template\|placeholder"; then
    echo -e "${RED}FALHA${NC} - Credenciais ou padrões sensíveis encontrados!"
    FAIL=1
else
    echo -e "${GREEN}OK${NC}"
fi

# 5. Verificar se há notebooks com credenciais hardcoded
echo -n "✓ Verificando notebooks... "
if find notebooks -name "*.ipynb" -type f -exec grep -l "AKIA\|01NgAk\|password.*=" {} \; 2>/dev/null | head -1; then
    echo -e "${YELLOW}AVISO${NC} - Verifique notebooks manualmente para credenciais"
    # FAIL=1  # Apenas aviso
else
    echo -e "${GREEN}OK${NC}"
fi

# 6. Verificar .gitignore está configurado corretamente
echo -n "✓ Verificando .gitignore... "
if grep -q "\.env" .gitignore && grep -q "connectors.*\.config" .gitignore; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FALHA${NC} - .gitignore não está configurado corretamente!"
    FAIL=1
fi

# 7. Verificar que .example estão presentes
echo -n "✓ Verificando .example templates... "
if [ -f ".env_kafka_connect.example" ] && [ -f "spark/.env.example" ]; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FALHA${NC} - Arquivos .example não encontrados!"
    FAIL=1
fi

echo
echo "======================================="
if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✓ Segurança OK - Seguro para fazer commit!${NC}"
    exit 0
else
    echo -e "${RED}✗ Problemas de segurança detectados!${NC}"
    echo "Resolva os problemas acima antes de fazer push."
    exit 1
fi
