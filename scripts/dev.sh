#!/bin/bash

# Script simplificado para desenvolvimento da aplicação Potato Identifier

set -e

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

deploy_remote() {
    print_info "Fazendo deploy na placa Torizon..."
    
    # Verificar se o contexto do Docker remoto está configurado
    if ! docker context ls | grep -q "torizon"; then
        print_warning "Contexto Docker remoto não encontrado!"
        print_info "Configure primeiro com:"
        echo "docker context create torizon --docker \"host=ssh://torizon@verdin-imx8mp-15247232\""
        return 1
    fi
    
    # Usar contexto remoto
    print_info "Mudando para contexto remoto..."
    docker context use torizon
    
    # Construir para ARM64
    print_info "Construindo para ARM64..."
    docker build -f Dockerfile -t kassiell/potato-identifier:arm64 --platform linux/arm64 .
    
    # Executar na placa
    print_info "Executando na placa..."
    docker run --rm -it \
        --device /dev/video0:/dev/video0 \
        --device /dev/video1:/dev/video1 \
        --privileged \
        --name potato-identifier \
        kassiell/potato-identifier:arm64
    
    # Voltar para contexto local
    docker context use default
    print_success "Deploy concluído!"
}

show_help() {
    cat << EOF
Potato Identifier - Script de Desenvolvimento Simplificado

Uso: $0 [OPÇÃO]

OPÇÕES:
    setup           Configura ambiente local
    check           Verifica sistema
    build           Constrói imagem Docker
    run             Executa aplicação
    test            Testa sistema local
    check-npu       Verifica sistema NPU
    setup-camera    Configura câmera no WSL2
    test-camera     Testa conexão da câmera
    test-usb        Testa câmeras USB disponíveis
    deploy          Deploy remoto na placa Torizon
    help            Mostra esta ajuda

EOF
}

# Função para detectar arquitetura Docker
get_docker_arch() {
    case "$(uname -m)" in
        x86_64)
            echo "amd64"
            ;;
        aarch64|arm64)
            echo "arm64"
            ;;
        armv7l)
            echo "arm"
            ;;
        *)
            echo "$(uname -m)"
            ;;
    esac
}

# Função para verificar se é desenvolvimento local
is_development_platform() {
    [[ "$(get_docker_arch)" == "amd64" ]]
}

setup_environment() {
    print_info "Configurando ambiente..."
    
    if [ ! -d ".venv" ]; then
        python3 -m venv .venv
    fi
    
    # source .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements-local.txt
    
    print_success "Ambiente configurado!"
}

check_system() {
    print_info "Verificando sistema..."
    
    if [ -f ".venv/bin/python" ]; then
        .venv/bin/python src/test_system.py
    else
        python3 src/test_system.py
    fi
}

build_image() {
    print_info "Construindo imagem Docker..."
    
    # Detecta se é para desenvolvimento local ou produção
    if is_development_platform; then
        print_info "Construindo para desenvolvimento local ($(get_docker_arch))..."
        unset DOCKER_HOST
        docker build -f Dockerfile.dev -t kassiell/potato-identifier:dev .
    else
        print_info "Construindo para produção ($(get_docker_arch))..."
        docker build -f Dockerfile -t kassiell/potato-identifier .
    fi
    
    print_success "Imagem construída!"
}

run_application() {
    print_info "Executando aplicação..."
    
    # Detecta se é desenvolvimento local ou produção
    if is_development_platform; then
        print_info "Executando localmente (desenvolvimento $(get_docker_arch))..."
        unset DOCKER_HOST
        
        # Configurar X11 forwarding para GUI
        print_info "Configurando acesso X11..."
        
        # Método mais robusto para X11 forwarding
        XSOCK=/tmp/.X11-unix
        XAUTH_FILE=/tmp/.docker.xauth
        
        # Criar arquivo de autorização temporário
        touch $XAUTH_FILE
        xauth nlist $DISPLAY | sed -e 's/^..../ffff/' | xauth -f $XAUTH_FILE nmerge -
        
        # Permitir acesso local
        xhost +local:docker 2>/dev/null || print_warning "Não foi possível configurar xhost"
        
        # Verificar dispositivos de vídeo disponíveis
        print_info "Verificando dispositivos de câmera..."
        VIDEO_DEVICES=""
        if ls /dev/video* >/dev/null 2>&1; then
            print_info "Dispositivos encontrados: $(ls /dev/video* | tr '\n' ' ')"
            
            # Verificar se o usuário tem acesso ao grupo video
            if ! groups | grep -q video; then
                print_warning "Usuário não está no grupo 'video'. Pode ser necessário adicionar manualmente:"
                print_warning "sudo usermod -a -G video $USER && newgrp video"
            fi
            
            # Adicionar dispositivos de vídeo ao comando Docker
            VIDEO_DEVICES=$(ls /dev/video* 2>/dev/null | sed 's/^/--device /' | tr '\n' ' ')
        else
            print_warning "Nenhum dispositivo /dev/video* encontrado"
        fi
        
        # Executar container com configuração X11 robusta
        docker run --rm -it \
            -e DISPLAY=$DISPLAY \
            -e XAUTHORITY=$XAUTH_FILE \
            -v $XSOCK:$XSOCK:rw \
            -v $XAUTH_FILE:$XAUTH_FILE:rw \
            --device-cgroup-rule='c 81:* rmw' \
            $VIDEO_DEVICES \
            --privileged \
            --name potato-identifier-dev \
            kassiell/potato-identifier:dev
            
        # Limpar arquivo de autorização temporário
        rm -f $XAUTH_FILE
    else
        print_info "Executando em produção ($(get_docker_arch))..."
        docker compose -f docker-compose.prod.yml up
    fi
}

test_local() {
    print_info "Testando aplicação local..."
    
    if [ -f ".venv/bin/python" ]; then
        .venv/bin/python src/test_system.py
        .venv/bin/python src/check_npu.py
    else
        python3 src/test_system.py
        python3 src/check_npu.py
    fi
}

# Verificar NPU
check_npu() {
    print_info "Verificando sistema NPU..."
    
    cd "$PROJECT_ROOT"
    
    if [[ -d ".venv" ]]; then
        source .venv/bin/activate
        python src/check_npu.py
    else
        print_warning "Ambiente virtual não encontrado. Execute: $0 setup"
        python3 src/check_npu.py
    fi
}

# Configurar câmera no WSL2
setup_camera() {
    print_info "Configurando acesso à câmera no WSL2..."
    
    print_info "Verificando dispositivos USB..."
    if command -v lsusb &> /dev/null; then
        lsusb
    else
        print_warning "lsusb não disponível, instalando..."
        sudo apt update && sudo apt install -y usbutils
        lsusb
    fi
    
    print_info "Verificando dispositivos de vídeo..."
    ls -la /dev/video* 2>/dev/null || print_warning "Nenhum dispositivo /dev/video* encontrado"
    
    print_info "Verificando acesso USB..."
    ls -la /dev/bus/usb/ 2>/dev/null || print_warning "Estrutura USB não disponível"
    
    print_info "Configurando permissões..."
    sudo usermod -a -G dialout $USER || true
    
    echo ""
    print_info "INSTRUÇÕES PARA WINDOWS:"
    echo "1. Abra PowerShell como Administrador"
    echo "2. Execute: winget install --interactive --exact dorssel.usbipd-win"
    echo "3. Reinicie o Windows"
    echo "4. Execute: usbipd list"
    echo "5. Execute: usbipd bind --busid X-Y (substitua X-Y)"
    echo "6. Execute: usbipd attach --wsl --busid X-Y"
    echo ""
    print_info "Consulte SETUP_CAMERA_WSL2.md para detalhes completos"
}

# Testar câmera
test_camera() {
    print_info "Testando conexão da câmera..."
    
    cd "$PROJECT_ROOT"
    
    if [[ -d ".venv" ]]; then
        source .venv/bin/activate
    fi
    
    print_info "Verificando PyPylon..."
    python3 -c "
import sys
try:
    from pypylon import pylon
    
    # Tentar enumerar dispositivos
    tlFactory = pylon.TlFactory.GetInstance()
    devices = tlFactory.EnumerateDevices()
    
    print(f'Número de câmeras encontradas: {len(devices)}')
    
    if len(devices) > 0:
        for i, device in enumerate(devices):
            print(f'Câmera {i+1}: {device.GetFriendlyName()}')
            print(f'  - Serial: {device.GetSerialNumber()}')
            print(f'  - Modelo: {device.GetModelName()}')
        print('✅ Câmera(s) detectada(s) com sucesso!')
    else:
        print('❌ Nenhuma câmera Basler encontrada')
        print('💡 Verifique:')
        print('   - Câmera conectada ao USB')
        print('   - usbipd configurado no Windows')
        print('   - Dispositivo compartilhado com WSL2')
        
except ImportError as e:
    print(f'❌ Erro ao importar PyPylon: {e}')
    print('💡 Execute: pip install pypylon')
except Exception as e:
    print(f'❌ Erro ao acessar câmera: {e}')
    print('💡 Verifique configuração USB/IP')
"
}

# Testar câmeras USB
test_usb() {
    print_info "Testando câmeras USB disponíveis..."
    
    cd "$PROJECT_ROOT"
    
    if [[ -d ".venv" ]]; then
        source .venv/bin/activate
    fi
    
    python src/test_usb_camera.py
}

clean_environment() {
    print_info "Limpando ambiente..."
    docker compose down 2>/dev/null || true
    docker image rm kassiell/potato-identifier 2>/dev/null || true
    docker system prune -f
    print_success "Limpeza concluída!"
}

case "${1:-help}" in
    setup)
        setup_environment
        ;;
    check)
        check_system
        ;;
    build)
        build_image
        ;;
    run)
        run_application
        ;;
    test)
        test_local
        ;;
    check-npu)
        check_npu
        ;;
    setup-camera)
        setup_camera
        ;;
    test-camera)
        test_camera
        ;;
    test-usb)
        test_usb
        ;;
    deploy)
        deploy_remote
        ;;
    clean)
        clean_environment
        ;;
    help|*)
        show_help
        ;;
esac
