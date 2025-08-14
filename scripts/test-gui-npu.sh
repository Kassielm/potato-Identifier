#!/bin/bash

echo "🚀 Testando Potato Identifier com GUI OpenCV e NPU..."
echo "======================================================"

# Verificar se a imagem existe
echo "📦 Verificando imagem Docker..."
if docker images | grep -q "potato-identifier.*gui"; then
    echo "✅ Imagem potato-identifier:gui encontrada"
else
    echo "❌ Imagem não encontrada. Construindo..."
    docker build -f Dockerfile.gui -t potato-identifier:gui .
fi

# Parar containers existentes
echo "🛑 Parando containers existentes..."
docker-compose -f docker-compose.gui.yml down

# Iniciar aplicação
echo "🎯 Iniciando aplicação com GUI e NPU..."
docker-compose -f docker-compose.gui.yml up

echo "🏁 Teste finalizado!"
