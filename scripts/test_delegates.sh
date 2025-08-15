#!/bin/bash

# Script para testar a aplicação com diferentes configurações de delegate

echo "========================================="
echo "  Teste de Configurações de Delegate"
echo "========================================="

# Teste 1: Apenas CPU (delegates desabilitados)
echo ""
echo "🧪 Teste 1: CPU apenas (DISABLE_DELEGATES=1)"
echo "----------------------------------------"
export DISABLE_DELEGATES=1
export NPU_AVAILABLE=0
export GUI_AVAILABLE=0
export HEADLESS=1
echo "Configuração:"
echo "  DISABLE_DELEGATES=1"
echo "  NPU_AVAILABLE=0" 
echo "  HEADLESS=1"
echo ""
echo "Executando teste..."
timeout 30s python src/main.py
test1_result=$?
echo "Resultado do Teste 1: $test1_result"

# Teste 2: NPU habilitado mas delegates desabilitados
echo ""
echo "🧪 Teste 2: NPU habilitado, delegates desabilitados"
echo "------------------------------------------------"
export DISABLE_DELEGATES=1
export NPU_AVAILABLE=1
export GUI_AVAILABLE=0
export HEADLESS=1
echo "Configuração:"
echo "  DISABLE_DELEGATES=1"
echo "  NPU_AVAILABLE=1"
echo "  HEADLESS=1"
echo ""
echo "Executando teste..."
timeout 30s python src/main.py
test2_result=$?
echo "Resultado do Teste 2: $test2_result"

# Teste 3: NPU e delegates habilitados
echo ""
echo "🧪 Teste 3: NPU e delegates habilitados"
echo "--------------------------------------"
export DISABLE_DELEGATES=0
export NPU_AVAILABLE=1
export GUI_AVAILABLE=0
export HEADLESS=1
echo "Configuração:"
echo "  DISABLE_DELEGATES=0"
echo "  NPU_AVAILABLE=1"
echo "  HEADLESS=1"
echo ""
echo "Executando teste..."
timeout 30s python src/main.py
test3_result=$?
echo "Resultado do Teste 3: $test3_result"

# Resumo
echo ""
echo "========================================="
echo "             RESUMO DOS TESTES"
echo "========================================="
echo "Teste 1 (CPU apenas): $test1_result"
echo "Teste 2 (NPU sem delegates): $test2_result"
echo "Teste 3 (NPU com delegates): $test3_result"
echo ""

if [ $test1_result -eq 0 ]; then
    echo "✅ CPU funciona corretamente"
else
    echo "❌ Problema com modo CPU"
fi

if [ $test2_result -eq 0 ]; then
    echo "✅ NPU sem delegates funciona corretamente"
else
    echo "❌ Problema com NPU sem delegates"
fi

if [ $test3_result -eq 0 ]; then
    echo "✅ NPU com delegates funciona corretamente"
else
    echo "❌ Problema com NPU e delegates"
fi

echo ""
echo "Para uso normal, recomende:"
if [ $test3_result -eq 0 ]; then
    echo "  export NPU_AVAILABLE=1"
    echo "  export DISABLE_DELEGATES=0"
elif [ $test2_result -eq 0 ]; then
    echo "  export NPU_AVAILABLE=1"
    echo "  export DISABLE_DELEGATES=1"
else
    echo "  export NPU_AVAILABLE=0"
    echo "  export DISABLE_DELEGATES=1"
fi
