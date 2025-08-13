#!/bin/bash

# Script para facilitar o desenvolvimento e teste da aplicação Potato Identifier

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para imprimir mensagens coloridas
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Função de ajuda
show_help() {
    cat << EOF
Potato Identifier - Script de Desenvolvimento

Uso: $0 [OPÇÃO]

OPÇÕES:
    setup           Configura o ambiente de desenvolvimento
    check-deps      Verifica dependências do sistema
    check-npu       Verifica suporte à NPU/EdgeTPU
    build-local     Constrói imagem Docker para desenvolvimento local
    build-prod      Constrói imagem Docker para produção (Toradex)
    run-local       Executa aplicação localmente (desenvolvimento)
    run-prod        Executa aplicação na placa Toradex
    test-plc        Testa conexão com PLC
    logs            Mostra logs da aplicação
    clean           Remove containers e imagens
    help            Mostra esta ajuda

EXEMPLOS:
    $0 setup        # Configura ambiente de desenvolvimento
    $0 run-local    # Executa aplicação localmente
    $0 run-prod     # Deploya na placa Toradex

EOF
}

# Função para configurar ambiente
setup_environment() {
    print_status "Configurando ambiente de desenvolvimento..."
    
    # Verificar se Python virtual env existe
    if [ ! -d ".venv" ]; then
        print_status "Criando ambiente virtual Python..."
        python3 -m venv .venv
    fi
    
    # Ativar ambiente virtual e instalar dependências
    print_status "Instalando dependências..."
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements-local.txt
    
    print_success "Ambiente configurado com sucesso!"
}

# Função para verificar dependências
check_dependencies() {
    print_status "Verificando dependências do sistema..."
    
    # Verificar Docker
    if command -v docker &> /dev/null; then
        print_success "Docker encontrado: $(docker --version)"
    else
        print_error "Docker não encontrado! Instale o Docker primeiro."
        exit 1
    fi
    
    # Verificar Docker Compose
    if command -v docker &> /dev/null && docker compose version &> /dev/null; then
        print_success "Docker Compose encontrado: $(docker compose version)"
    elif command -v docker-compose &> /dev/null; then
        print_success "Docker Compose encontrado: $(docker-compose --version)"
    else
        print_error "Docker Compose não encontrado! Instale o Docker Compose primeiro."
        exit 1
    fi
    
    # Verificar Python
    if command -v python3 &> /dev/null; then
        print_success "Python encontrado: $(python3 --version)"
    else
        print_error "Python3 não encontrado! Instale o Python3 primeiro."
        exit 1
    fi
    
    print_success "Todas as dependências principais estão disponíveis!"
}

# Função para verificar NPU
check_npu() {
    print_status "Verificando suporte à NPU/EdgeTPU..."
    
    if [ -f ".venv/bin/python" ]; then
        .venv/bin/python src/check_npu.py
    else
        python3 src/check_npu.py
    fi
}

# Função para construir imagem local
build_local() {
    print_status "Construindo imagem Docker para desenvolvimento local..."
    docker compose -f docker-compose.dev.yml build
    print_success "Imagem local construída com sucesso!"
}

# Função para construir imagem de produção
build_production() {
    print_status "Construindo imagem Docker para produção (Toradex)..."
    docker compose -f docker-compose.yml build
    print_success "Imagem de produção construída com sucesso!"
}

# Função para executar localmente
run_local() {
    print_status "Executando aplicação localmente..."
    docker compose -f docker-compose.dev.yml up --build
}

# Função para executar em produção
run_production() {
    print_status "Executando aplicação na placa Toradex..."
    docker compose -f docker-compose.prod.yml up
}

# Função para testar PLC
test_plc() {
    print_status "Testando conexão com PLC..."
    
    cat << 'EOF' > /tmp/test_plc.py
import sys
sys.path.append('src')
from plc import Plc

plc = Plc()
if plc.init_plc():
    print("✓ Conexão com PLC estabelecida com sucesso!")
    plc.write_db(0)
    print("✓ Teste de escrita no PLC realizado!")
    plc.disconnect()
else:
    print("✗ Falha ao conectar com PLC")
    sys.exit(1)
EOF
    
    if [ -f ".venv/bin/python" ]; then
        .venv/bin/python /tmp/test_plc.py
    else
        python3 /tmp/test_plc.py
    fi
    
    rm -f /tmp/test_plc.py
}

# Função para mostrar logs
show_logs() {
    print_status "Mostrando logs da aplicação..."
    docker compose logs -f potato-identifier
}

# Função para limpeza
clean_environment() {
    print_status "Limpando containers e imagens..."
    
    # Parar containers
    docker compose -f docker-compose.yml down 2>/dev/null || true
    docker compose -f docker-compose.dev.yml down 2>/dev/null || true
    docker compose -f docker-compose.prod.yml down 2>/dev/null || true
    
    # Remover imagens
    docker image rm kassiell/potato-identifier:dev 2>/dev/null || true
    docker image rm kassiell/potato-identifier 2>/dev/null || true
    
    # Remover containers orfãos
    docker system prune -f
    
    print_success "Limpeza concluída!"
}

# Main script
case "${1:-help}" in
    setup)
        check_dependencies
        setup_environment
        ;;
    check-deps)
        check_dependencies
        ;;
    check-npu)
        check_npu
        ;;
    build-local)
        build_local
        ;;
    build-prod)
        build_production
        ;;
    run-local)
        run_local
        ;;
    run-prod)
        run_production
        ;;
    test-plc)
        test_plc
        ;;
    logs)
        show_logs
        ;;
    clean)
        clean_environment
        ;;
    help|*)
        show_help
        ;;
esac
