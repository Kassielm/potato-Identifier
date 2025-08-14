# Potato Identifier - Configuração NPU para Verdin iMX8MP

Este projeto foi configurado para usar automaticamente a aceleração de hardware disponível na placa Toradex Verdin iMX8MP.

## 🚀 Configuração Automática de Delegates

A aplicação detecta automaticamente os delegates de aceleração disponíveis na seguinte ordem de prioridade:

1. **NPU específico iMX** (`libimxnn_delegate.so`) - Melhor performance
2. **Ethos-U NPU** (`libethosu_delegate.so`) - NPU ARM 
3. **VX GPU/VPU** (`libvx_delegate.so`) - Aceleração GPU
4. **CPU** - Fallback sem aceleração

## 📋 Verificação do Sistema

Para verificar se sua placa está configurada corretamente:

```bash
# Execute o script de diagnóstico
python3 scripts/check_delegates.py
```

Este script verifica:
- ✅ Informações do processador iMX8MP
- ✅ Delegates de aceleração disponíveis
- ✅ Versões do TensorFlow Lite e OpenCV
- ✅ Teste de carregamento dos delegates

## 🔧 Performance Esperada

| Modo | Tempo de Inferência | Uso |
|------|-------------------|-----|
| NPU | 15-30ms | Melhor opção |
| GPU/VPU | 25-60ms | Boa opção |
| CPU | 150-300ms | Fallback |

## 🐳 Execução com Docker

O Dockerfile está configurado para usar automaticamente a aceleração disponível:

```bash
# Build da imagem
docker build -t potato-identifier .

# Execução (com acesso aos dispositivos de hardware)
docker run --privileged --device=/dev/dri:/dev/dri potato-identifier
```

## 📊 Logs de Performance

A aplicação mostra logs indicando o delegate carregado:

```
✅ Delegate VX GPU/VPU carregado: '/usr/lib/libvx_delegate.so'
⚡ Tempo médio de inferência: 25.3ms
🚀 Performance excelente - delegate de hardware funcionando!
```

## 🔍 Troubleshooting

### Problema: Nenhum delegate encontrado
**Solução**: Verifique se você está usando uma imagem Torizon atualizada com suporte a aceleração.

### Problema: Delegate não carrega
**Solução**: Execute o script de diagnóstico para verificar permissões e dependências.

### Problema: Performance baixa
**Solução**: Verifique se o modelo é quantizado (INT8) para melhor performance na NPU.

## 📚 Modelos Suportados

- ✅ `best_int8.tflite` - Otimizado para NPU (recomendado)
- ✅ `best_float32.tflite` - Para GPU/CPU
- ✅ `best_float32_edgetpu.tflite` - Para Edge TPU (se disponível)

## 🛠️ Desenvolvimento

Para desenvolver localmente:

```bash
# Instalar dependências
pip install -r requirements-local.txt

# Executar aplicação
python3 src/main.py

# Verificar sistema
python3 scripts/check_delegates.py
```

## 📞 Suporte

- [Documentação Toradex](https://developer.toradex.com)
- [Community Toradex](https://community.toradex.com)
- [Torizon Developer Website](https://developer.toradex.com/torizon)
