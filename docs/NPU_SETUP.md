# Configuração de NPU para Verdin iMX8MP

Este documento explica como configurar e usar a NPU (Neural Processing Unit) da placa Toradex Verdin iMX8MP com sua aplicação de visão computacional.

## 🎯 O que foi modificado

### 1. Detecção automática de delegates

A aplicação agora detecta automaticamente os delegates de aceleração disponíveis no sistema:

- **NPU iMX específico**: `/usr/lib/libimxnn_delegate.so`
- **Ethos-U NPU**: `/usr/lib/libethosu_delegate.so`
- **VX GPU/VPU**: `/usr/lib/libvx_delegate.so` (várias localizações)
- **Fallback para CPU**: Se nenhum delegate estiver disponível

### 2. Função de detecção de delegates

```python
def detect_available_delegates():
    """Detecta delegates de aceleração disponíveis no sistema Verdin iMX8MP."""
```

Esta função verifica automaticamente quais delegates estão disponíveis e retorna o melhor disponível.

### 3. Inicialização melhorada do modelo

O código agora:
- ✅ Detecta e carrega diferentes tipos de delegates
- ✅ Fornece feedback detalhado sobre qual delegate foi carregado
- ✅ Testa a performance para verificar se a aceleração está funcionando
- ✅ Faz fallback para CPU se necessário

### 4. Dockerfile atualizado

Adicionadas dependências para aceleração de hardware:
```dockerfile
libopenvx-c1 \
libopenvx-dev \
libvx-dev \
libneuralnetworks1 \
```

## 🚀 Como usar

### 1. Execute o verificador de delegates

Primeiro, execute o script de verificação para diagnosticar seu sistema:

```bash
python3 scripts/check_delegates.py
```

Este script irá:
- Verificar informações do sistema
- Listar delegates disponíveis
- Testar o carregamento dos delegates
- Fornecer um diagnóstico completo

### 2. Execute sua aplicação

A aplicação agora detecta automaticamente o melhor delegate:

```bash
python3 src/main.py
```

Você verá logs como:
```
2025-01-XX XX:XX:XX - INFO - Delegate encontrado: VX GPU/VPU em /usr/lib/libvx_delegate.so
2025-01-XX XX:XX:XX - INFO - ✅ Delegate VX GPU/VPU carregado: '/usr/lib/libvx_delegate.so'
2025-01-XX XX:XX:XX - INFO - ⚡ Tempo médio de inferência: 25.3ms
2025-01-XX XX:XX:XX - INFO - 🚀 Performance excelente - delegate de hardware funcionando!
```

## 🔧 Solução de problemas

### Problema: Nenhum delegate encontrado

**Sintomas:**
```
⚠️ Nenhum delegate de aceleração encontrado. Usando CPU.
🐌 Performance lenta - verificar se delegate está funcionando
```

**Soluções:**

1. **Verificar se está no Torizon correto:**
   ```bash
   cat /etc/os-release
   ```
   Deve mostrar uma versão do Torizon com suporte ao iMX8MP.

2. **Instalar pacotes de aceleração:**
   ```bash
   sudo apt update
   sudo apt install libopenvx-c1 libopenvx-dev libvx-dev
   ```

3. **Verificar se os arquivos de delegate existem:**
   ```bash
   find /usr/lib -name "*vx_delegate*" -o -name "*imxnn*" -o -name "*ethosu*"
   ```

### Problema: Delegate carregado mas performance ruim

**Sintomas:**
```
✅ Delegate VX GPU/VPU carregado
🐌 Performance lenta - verificar se delegate está funcionando
```

**Possíveis causas:**
1. Modelo não otimizado para a NPU
2. Delegate não compatível com o modelo
3. Configuração do sistema

**Soluções:**

1. **Usar modelo quantizado INT8:**
   Certifique-se de usar `best_int8.tflite` em vez de modelos float32.

2. **Verificar compatibilidade do modelo:**
   Alguns modelos podem não ser totalmente suportados pelo delegate.

3. **Testar diferentes delegates:**
   Modifique temporariamente a ordem em `detect_available_delegates()`.

### Problema: Erro ao carregar delegate

**Sintomas:**
```
❌ Erro ao carregar o delegate: [ERRO ESPECÍFICO]
```

**Soluções:**

1. **Verificar permissões:**
   ```bash
   ls -la /usr/lib/libvx_delegate.so
   ```

2. **Verificar dependências:**
   ```bash
   ldd /usr/lib/libvx_delegate.so
   ```

3. **Verificar logs do sistema:**
   ```bash
   dmesg | grep -i vx
   dmesg | grep -i gpu
   ```

## 📊 Benchmarks esperados

### Performance típica no Verdin iMX8MP:

| Configuração | Tempo de Inferência | Uso |
|-------------|-------------------|-----|
| CPU (ARM Cortex-A53) | ~150-300ms | Fallback |
| VX GPU/VPU | ~30-60ms | Recomendado |
| NPU específico | ~15-30ms | Melhor (se disponível) |

*Tempos para modelo YOLO 640x640 INT8*

### Indicadores de sucesso:

- ✅ **< 50ms**: Excelente - aceleração de hardware funcionando
- ✅ **50-100ms**: Bom - possível aceleração parcial
- ⚠️ **> 100ms**: Lento - verificar configuração

## 🔗 Referências úteis

### Toradex
- [Documentação oficial Verdin iMX8MP](https://developer.toradex.com/hardware/verdin-som-family)
- [Torizon Documentation](https://developer.toradex.com/torizon)

### NXP iMX8MP
- [i.MX 8M Plus Applications Processor](https://www.nxp.com/products/processors-and-microcontrollers/arm-processors/i-mx-applications-processors/i-mx-8-family/i-mx-8m-plus-family:i.MX8MPLUS)
- [Machine Learning Documentation](https://www.nxp.com/design/software/embedded-software/i-mx-machine-learning:i.MX-MACHINE-LEARNING)

### TensorFlow Lite
- [TensorFlow Lite Delegates](https://www.tensorflow.org/lite/performance/delegates)
- [Hardware acceleration](https://www.tensorflow.org/lite/performance/gpu)

## 🆘 Suporte

Se você ainda tiver problemas:

1. Execute `python3 scripts/check_delegates.py` e compartilhe a saída
2. Verifique os logs completos da aplicação
3. Consulte a comunidade Toradex: https://community.toradex.com/

---

**Nota:** Esta configuração foi otimizada especificamente para a placa Toradex Verdin iMX8MP rodando Torizon OS. Outras placas podem precisar de ajustes diferentes.
