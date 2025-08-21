#!/bin/bash

# Script para resolver problemas com NPU e delegates do TensorFlow Lite
# Autor: GitHub Copilot
# Versão: 1.0

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funções auxiliares
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar se estamos no diretório correto
if [ ! -f "docker-compose.yml" ]; then
    log_error "Execute este script no diretório raiz do projeto"
    exit 1
fi

show_help() {
    echo "🛠️  Script de Resolução de Problemas NPU"
    echo "======================================"
    echo ""
    echo "Uso: $0 [comando]"
    echo ""
    echo "Comandos disponíveis:"
    echo "  diagnose      - Executar diagnóstico completo do NPU"
    echo "  test-models   - Testar todos os modelos disponíveis"
    echo "  run-cpu       - Executar aplicação forçando CPU apenas"
    echo "  run-npu       - Executar aplicação com NPU (padrão)"
    echo "  stop          - Parar todos os containers"
    echo "  logs          - Mostrar logs do container"
    echo "  shell         - Abrir shell no container"
    echo "  fix-perms     - Corrigir permissões de dispositivos"
    echo "  clean         - Limpar containers e imagens antigas"
    echo "  help          - Mostrar esta ajuda"
    echo ""
}

diagnose_system() {
    log_info "🔍 Executando diagnóstico do sistema..."
    
    # Verificar se o container está rodando
    if docker ps | grep -q "potato-identifier"; then
        log_info "Container encontrado, executando diagnóstico interno..."
        docker exec -it potato-identifier-gui python3 /app/scripts/diagnose_npu.py
    else
        log_warning "Container não está rodando, iniciando container temporário..."
        docker run --rm -it \
            --privileged \
            -v /dev:/dev:rw \
            -e NPU_AVAILABLE=1 \
            kassiell/potato-identifier:2.3 \
            python3 /app/scripts/diagnose_npu.py
    fi
}

test_models() {
    log_info "🧪 Testando modelos TensorFlow Lite..."
    
    if docker ps | grep -q "potato-identifier"; then
        log_info "Executando teste de modelos no container..."
        docker exec -it potato-identifier-gui python3 /app/scripts/test_models.py
    else
        log_warning "Container não está rodando, iniciando container temporário..."
        docker run --rm -it \
            --privileged \
            -v /dev:/dev:rw \
            -e NPU_AVAILABLE=1 \
            kassiell/potato-identifier:2.3 \
            python3 /app/scripts/test_models.py
    fi
}

run_cpu_only() {
    log_info "🖥️  Executando aplicação em modo CPU apenas..."
    
    # Parar containers existentes
    docker compose down 2>/dev/null || true
    
    # Executar com CPU apenas
    log_info "Iniciando container com CPU apenas..."
    docker compose -f docker-compose.cpu.yml up -d
    
    log_success "Container iniciado em modo CPU. Use '$0 logs' para ver os logs."
}

run_with_npu() {
    log_info "🧠 Executando aplicação com NPU..."
    
    # Parar containers existentes
    docker compose -f docker-compose.cpu.yml down 2>/dev/null || true
    docker compose down 2>/dev/null || true
    
    # Executar com NPU
    log_info "Iniciando container com NPU..."
    docker compose up -d
    
    log_success "Container iniciado com NPU. Use '$0 logs' para ver os logs."
}

stop_containers() {
    log_info "🛑 Parando todos os containers..."
    
    docker compose down 2>/dev/null || true
    docker compose -f docker-compose.cpu.yml down 2>/dev/null || true
    
    log_success "Todos os containers foram parados."
}

show_logs() {
    log_info "📋 Mostrando logs dos containers..."
    
    if docker ps | grep -q "potato-identifier-gui"; then
        docker logs -f potato-identifier-gui
    elif docker ps | grep -q "potato-identifier-cpu"; then
        docker logs -f potato-identifier-cpu
    else
        log_error "Nenhum container está rodando."
        exit 1
    fi
}

open_shell() {
    log_info "🐚 Abrindo shell no container..."
    
    if docker ps | grep -q "potato-identifier-gui"; then
        docker exec -it potato-identifier-gui /bin/bash
    elif docker ps | grep -q "potato-identifier-cpu"; then
        docker exec -it potato-identifier-cpu /bin/bash
    else
        log_error "Nenhum container está rodando."
        log_info "Iniciando container temporário..."
        docker run --rm -it \
            --privileged \
            -v /dev:/dev:rw \
            kassiell/potato-identifier:2.3 \
            /bin/bash
    fi
}

fix_permissions() {
    log_info "🔧 Corrigindo permissões de dispositivos..."
    
    # Verificar dispositivos importantes
    devices=("/dev/vipnpu" "/dev/video0" "/dev/video1" "/dev/video2")
    
    for device in "${devices[@]}"; do
        if [ -e "$device" ]; then
            log_info "Corrigindo permissões de $device..."
            sudo chmod 666 "$device" 2>/dev/null || log_warning "Não foi possível alterar permissões de $device"
        else
            log_warning "Dispositivo $device não encontrado"
        fi
    done
    
    log_success "Permissões de dispositivos corrigidas."
}

clean_docker() {
    log_info "🧹 Limpando containers e imagens antigas..."
    
    # Parar containers
    stop_containers
    
    # Remover containers órfãos
    docker system prune -f
    
    # Remover imagens antigas do projeto
    docker images | grep "potato-identifier" | grep -v "2.3" | awk '{print $3}' | xargs -r docker rmi -f
    
    log_success "Limpeza concluída."
}

# Função principal
main() {
    case "${1:-help}" in
        "diagnose")
            diagnose_system
            ;;
        "test-models")
            test_models
            ;;
        "run-cpu")
            run_cpu_only
            ;;
        "run-npu")
            run_with_npu
            ;;
        "stop")
            stop_containers
            ;;
        "logs")
            show_logs
            ;;
        "shell")
            open_shell
            ;;
        "fix-perms")
            fix_permissions
            ;;
        "clean")
            clean_docker
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# Executar função principal
main "$@"
