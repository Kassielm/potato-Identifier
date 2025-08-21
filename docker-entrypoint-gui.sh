#!/bin/bash
set -e

echo "🖥️  Configurando ambiente gráfico para Toradex..."

# Aguardar o Weston estar pronto
echo "⏳ Aguardando compositor Weston..."
timeout_count=0
max_timeout=30  # Aguarda no máximo 30 segundos

while [ ! -S /tmp/wayland-0 ] && [ ! -S /tmp/1000-runtime-dir/wayland-0 ] && [ $timeout_count -lt $max_timeout ]; do
    sleep 1
    timeout_count=$((timeout_count + 1))
    echo "⏳ Aguardando Weston... ($timeout_count/$max_timeout)"
done

if [ $timeout_count -eq $max_timeout ]; then
    echo "⚠️  Timeout aguardando Weston compositor. Continuando sem interface gráfica..."
    echo "📱 Aplicação executará em modo headless"
fi

# Detectar localização do socket Wayland
if [ -S /tmp/1000-runtime-dir/wayland-0 ]; then
    echo "✅ Socket Wayland encontrado em /tmp/1000-runtime-dir/wayland-0"
    export WAYLAND_DISPLAY=wayland-0
    export XDG_RUNTIME_DIR=/tmp/1000-runtime-dir
elif [ -S /tmp/wayland-0 ]; then
    echo "✅ Socket Wayland encontrado em /tmp/wayland-0"
    export WAYLAND_DISPLAY=wayland-0
    export XDG_RUNTIME_DIR=/tmp
else
    echo "⚠️  Nenhum socket Wayland encontrado - modo headless"
    echo "📱 Configurando para execução sem display"
    export DISPLAY=""
    export WAYLAND_DISPLAY=""
    export XDG_RUNTIME_DIR=/tmp
fi

# Configurar permissões de câmera (com privilégios root)
echo "📷 Configurando permissões de câmera..."
chmod 666 /dev/video* 2>/dev/null || true

# Verificar câmeras após configurar permissões
echo "📷 Verificando acesso à câmera..."
for i in /dev/video*; do
    if [ -e "$i" ]; then
        echo "   ✅ Câmera detectada: $i ($(ls -la $i | awk '{print $1, $3, $4}'))"
    fi
done

# Configurar GPU permissions
echo "🔧 Configurando permissões GPU..."
chmod 666 /dev/dri/* 2>/dev/null || true
chmod 666 /dev/galcore 2>/dev/null || true

# Configurar permissões X11 para tkinter
echo "🔧 Configurando permissões X11..."
chmod 777 /tmp/.X11-unix 2>/dev/null || true
chmod 666 /tmp/.X11-unix/* 2>/dev/null || true

# Verificar NPU
echo "🧠 Verificando disponibilidade da NPU..."
if [ -e /sys/bus/platform/devices/38500000.vipsi ] || [ -e /sys/devices/platform/*vipsi* ] 2>/dev/null; then
    export NPU_AVAILABLE=1
    echo "   ✅ NPU detectada (VIP)"
elif grep -q "imx8mp" /proc/cpuinfo 2>/dev/null; then
    export NPU_AVAILABLE=1
    echo "   ✅ NPU detectada (i.MX8MP)"
else
    export NPU_AVAILABLE=0
    echo "   ⚠️  NPU não detectada"
fi

# Configurar variáveis de ambiente para GUI
# OpenCV precisa de XCB para Qt, mas mantemos Wayland para outros componentes
export GDK_BACKEND=wayland
export QT_QPA_PLATFORM=xcb
export SDL_VIDEODRIVER=wayland
export XDG_SESSION_TYPE=wayland
export GUI_AVAILABLE=1
export HEADLESS=0

# Configurar modo de exibição da janela (1=tela cheia, 0=centralizada)
export FULLSCREEN_MODE=${FULLSCREEN_MODE:-1}

# Configurações específicas para OpenCV funcionar com Wayland/XCB
export QT_XCB_GL_INTEGRATION=none
export QT_LOGGING_RULES="*.debug=false"

echo "✅ OpenCV GUI configurado para XCB/Wayland"

echo "📊 Configuração do ambiente:"
echo "   XDG_RUNTIME_DIR: $XDG_RUNTIME_DIR"
echo "   WAYLAND_DISPLAY: $WAYLAND_DISPLAY"
echo "   GDK_BACKEND: $GDK_BACKEND"
echo "   QT_QPA_PLATFORM: $QT_QPA_PLATFORM"
echo "   GUI_AVAILABLE: $GUI_AVAILABLE"
echo "   NPU_AVAILABLE: $NPU_AVAILABLE"
echo "   HEADLESS: $HEADLESS"

echo "🚀 Iniciando aplicação Potato Identifier..."

# Ativar o ambiente virtual e executar aplicação
cd /app
source /opt/venv/bin/activate

echo "🔍 Verificando aplicação Python..."
python3 -c "import sys; print(f'Python: {sys.version}')"
python3 -c "import cv2; print(f'OpenCV: {cv2.__version__}')"

echo "🎯 Executando aplicação principal..."
python3 /app/src/main.py 2>&1 | tee /tmp/app.log

# Se chegou aqui, a aplicação terminou - mostrar logs e manter container vivo para debug
echo "❌ Aplicação terminou unexpectadamente!"
echo "📋 Últimas linhas do log:"
tail -20 /tmp/app.log
echo "🔄 Mantendo container vivo para debug..."
sleep infinity