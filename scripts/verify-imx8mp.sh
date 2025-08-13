#!/bin/bash

# Script de verificação para Toradex Verdin iMX8MP
# Verifica se todos os recursos necessários estão disponíveis

echo "🔍 Verificação do Sistema Toradex Verdin iMX8MP"
echo "=============================================="

# Verificar dispositivos NPU
echo ""
echo "🧠 NPU (Neural Processing Unit):"
if [ -e /dev/vipnpu ]; then
    echo "   ✅ NPU detectada: /dev/vipnpu"
    ls -la /dev/vipnpu*
else
    echo "   ❌ NPU não encontrada"
fi

# Verificar GPU Vivante
echo ""
echo "🎮 GPU Vivante:"
if [ -e /dev/galcore ]; then
    echo "   ✅ GPU Vivante detectada: /dev/galcore"
    ls -la /dev/galcore
else
    echo "   ❌ GPU Vivante não encontrada"
fi

# Verificar DRM/DRI
echo ""
echo "🖥️  Display (DRM/DRI):"
if [ -d /dev/dri ]; then
    echo "   ✅ DRI disponível:"
    ls -la /dev/dri/
else
    echo "   ❌ DRI não encontrado"
fi

# Verificar câmeras
echo ""
echo "📷 Câmeras:"
camera_found=false
for i in /dev/video*; do
    if [ -e "$i" ]; then
        echo "   ✅ Câmera encontrada: $i"
        camera_found=true
    fi
done

if [ "$camera_found" = false ]; then
    echo "   ❌ Nenhuma câmera encontrada"
fi

# Verificar Wayland
echo ""
echo "🪟 Wayland/Weston:"
if [ -S /tmp/wayland-0 ]; then
    echo "   ✅ Socket Wayland ativo: /tmp/wayland-0"
else
    echo "   ⚠️  Socket Wayland não encontrado"
fi

# Verificar variáveis de ambiente
echo ""
echo "🌍 Variáveis de Ambiente:"
echo "   DISPLAY: ${DISPLAY:-'não definido'}"
echo "   WAYLAND_DISPLAY: ${WAYLAND_DISPLAY:-'não definido'}"
echo "   XDG_RUNTIME_DIR: ${XDG_RUNTIME_DIR:-'não definido'}"

# Verificar módulos do kernel
echo ""
echo "🔧 Módulos do Kernel:"
echo "   Galcore (GPU):"
if lsmod | grep -q galcore; then
    echo "      ✅ Carregado"
    lsmod | grep galcore
else
    echo "      ❌ Não carregado"
fi

echo "   VIPNPU:"
if lsmod | grep -q vipnpu; then
    echo "      ✅ Carregado"
    lsmod | grep vipnpu
else
    echo "      ❌ Não carregado"
fi

# Verificar processos Docker
echo ""
echo "🐳 Docker Containers:"
if command -v docker >/dev/null 2>&1; then
    if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "(weston|potato)"; then
        echo "   ✅ Containers relacionados encontrados:"
        docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "(weston|potato)"
    else
        echo "   ⚠️  Nenhum container relacionado rodando"
    fi
else
    echo "   ❌ Docker não disponível"
fi

# Verificar recursos do sistema
echo ""
echo "💾 Recursos do Sistema:"
echo "   CPU:"
nproc
cat /proc/cpuinfo | grep "model name" | head -1

echo "   Memória:"
free -h | head -2

echo "   Espaço em disco:"
df -h / | tail -1

# Verificar rede
echo ""
echo "🌐 Rede:"
if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
    echo "   ✅ Conectividade externa OK"
else
    echo "   ⚠️  Sem conectividade externa"
fi

echo ""
echo "🏁 Verificação concluída!"
echo ""
echo "💡 Para iniciar a aplicação com GUI:"
echo "   docker-compose -f docker-compose.gui.yml up -d"
echo ""
echo "📊 Para monitorar logs:"
echo "   docker logs -f potato-identifier-gui"
