#!/bin/bash
set -e

echo "🖥️  Configurando ambiente gráfico para Toradex..."

# Aguardar o Weston estar pronto
echo "⏳ Aguardando compositor Weston..."
while [ ! -S /tmp/wayland-0 ]; do
    sleep 1
done

# Configurar permissões para dispositivos
echo "🔧 Configurando permissões de dispositivos..."
if [ -e /dev/dri ]; then
    chmod 666 /dev/dri/*
fi

if [ -e /dev/galcore ]; then
    chmod 666 /dev/galcore
fi

# Configurar acesso à câmera
echo "📷 Configurando acesso à câmera..."
for i in /dev/video*; do
    if [ -e "$i" ]; then
        chmod 666 "$i"
        echo "   Configurado: $i"
    fi
done

# Verificar NPU
echo "🧠 Verificando disponibilidade da NPU..."
if [ -e /dev/vipnpu* ]; then
    chmod 666 /dev/vipnpu*
    echo "   ✅ NPU detectada e configurada"
    export NPU_AVAILABLE=1
else
    echo "   ⚠️  NPU não detectada"
    export NPU_AVAILABLE=0
fi

# Configurar variáveis de ambiente para GUI
export DISPLAY=:0
export WAYLAND_DISPLAY=wayland-0
export XDG_RUNTIME_DIR=/tmp
export XDG_SESSION_TYPE=wayland

# Verificar se está em ambiente gráfico
if [ -S /tmp/wayland-0 ]; then
    echo "✅ Compositor Wayland detectado"
    export GUI_AVAILABLE=1
else
    echo "⚠️  Ambiente gráfico não detectado - executando em modo headless"
    export HEADLESS=1
    export GUI_AVAILABLE=0
fi

# Log de configuração
echo "📊 Configuração do ambiente:"
echo "   DISPLAY: $DISPLAY"
echo "   WAYLAND_DISPLAY: $WAYLAND_DISPLAY"
echo "   GUI_AVAILABLE: $GUI_AVAILABLE"
echo "   NPU_AVAILABLE: $NPU_AVAILABLE"
echo "   HEADLESS: ${HEADLESS:-0}"

echo "🚀 Iniciando aplicação Potato Identifier..."
exec "$@"
