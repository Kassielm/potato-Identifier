#!/bin/bash
set -e

echo "🖥️  Configurando ambiente gráfico para Toradex..."

# Aguardar o Weston estar pronto
echo "⏳ Aguardando compositor Weston..."
while [ ! -S /tmp/wayland-0 ] && [ ! -S /tmp/1000-runtime-dir/wayland-0 ]; do
    sleep 1
done

# Detectar localização do socket Wayland
if [ -S /tmp/1000-runtime-dir/wayland-0 ]; then
    echo "✅ Socket Wayland encontrado em /tmp/1000-runtime-dir/wayland-0"
    export WAYLAND_DISPLAY=wayland-0
    export XDG_RUNTIME_DIR=/tmp/1000-runtime-dir
elif [ -S /tmp/wayland-0 ]; then
    echo "✅ Socket Wayland encontrado em /tmp/wayland-0"
    export WAYLAND_DISPLAY=wayland-0
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
if [ -e /dev/vipnpu* ]; then
    export NPU_AVAILABLE=1
    echo "   ✅ NPU detectada"
else
    export NPU_AVAILABLE=0
    echo "   ⚠️  NPU não detectada"
fi

# Configurar variáveis de ambiente para GUI
# Para OpenCV GUI, focar em Wayland sem X11
export GDK_BACKEND=wayland
export QT_QPA_PLATFORM=wayland
export SDL_VIDEODRIVER=wayland
export XDG_SESSION_TYPE=wayland
export GUI_AVAILABLE=1
export HEADLESS=0

echo "✅ OpenCV GUI configurado para Wayland"

echo "📊 Configuração do ambiente:"
echo "   XDG_RUNTIME_DIR: $XDG_RUNTIME_DIR"
echo "   WAYLAND_DISPLAY: $WAYLAND_DISPLAY"
echo "   GDK_BACKEND: $GDK_BACKEND"
echo "   QT_QPA_PLATFORM: $QT_QPA_PLATFORM"
echo "   GUI_AVAILABLE: $GUI_AVAILABLE"
echo "   NPU_AVAILABLE: $NPU_AVAILABLE"
echo "   HEADLESS: $HEADLESS"

echo "🚀 Iniciando aplicação Potato Identifier..."

# Executar a aplicação como usuário torizon para compatibilidade
exec su torizon -c "cd /app && python3 /app/src/main.py"
