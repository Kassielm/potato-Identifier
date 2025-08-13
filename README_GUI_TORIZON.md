# Interface Gráfica na Toradex Verdin iMX8MP

## 🎯 Objetivo
Configurar e executar a aplicação Potato Identifier com interface gráfica diretamente na tela conectada à placa Toradex Verdin iMX8MP, utilizando a NPU para aceleração de inferência.

## 🏗️ Arquitetura

### Hardware Target
- **Placa**: Toradex Verdin iMX8MP
- **Carrier Board**: Dahlia Carrier Board
- **SoC**: NXP i.MX 8M Plus
- **NPU**: 2.3 TOPS Neural Processing Unit
- **GPU**: Vivante GC7000UL
- **Display**: Conectado via DSI/HDMI na Dahlia

### Software Stack
- **SO**: Torizon OS (baseado em Linux)
- **Compositor**: Weston (Wayland)
- **Container Runtime**: Docker
- **GUI Framework**: Tkinter (Python)
- **IA Engine**: TensorFlow Lite com EdgeTPU
- **Comunicação**: snap7 para PLC

## 🚀 Deploy e Execução

### 1. Configuração Inicial

#### SSH Key Setup (se necessário)
```bash
# Gerar chave SSH se não existir
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

# Copiar chave para a placa
ssh-copy-id torizon@<IP_DA_PLACA>
```

#### Docker Context
```bash
# Criar contexto para a placa
docker context create torizon --docker "host=ssh://torizon@<IP_DA_PLACA>"

# Verificar contextos
docker context ls
```

### 2. Build e Deploy

#### Build da Imagem GUI
```bash
# Build com interface gráfica
./scripts/dev.sh build-gui
```

#### Deploy Completo
```bash
# Deploy com Weston + GUI
./scripts/dev.sh deploy-gui
```

#### Deploy Manual (se necessário)
```bash
# Mudar para contexto remoto
docker context use torizon

# Executar docker-compose
docker-compose -f docker-compose.gui.yml up -d

# Voltar para contexto local
docker context use default
```

### 3. Monitoramento

#### Logs da Aplicação
```bash
docker context use torizon
docker logs -f potato-identifier-gui
```

#### Logs do Weston
```bash
docker logs -f weston
```

#### Status dos Containers
```bash
docker ps
```

## 🧠 NPU (Neural Processing Unit)

### Verificação da NPU
```bash
# Na placa, verificar dispositivos
ls -la /dev/vipnpu*

# Verificar se EdgeTPU está carregado
lsmod | grep galcore
```

### Modelos Suportados
- **EdgeTPU Model**: `best_float32_edgetpu.tflite` (para NPU)
- **CPU Fallback**: `best_float32.tflite` (para CPU)

### Performance Esperada
- **NPU**: ~2.3 TOPS, latência < 10ms
- **CPU**: ~100-200ms por inferência

## 🖥️ Interface Gráfica

### Recursos GUI
- **Display Output**: Direto na tela conectada
- **Resolução**: Automática (configurada pelo Weston)
- **Framework**: Tkinter com renderização via Wayland
- **Performance**: GPU Vivante para aceleração gráfica

### Troubleshooting GUI

#### Tela Preta/Sem Display
```bash
# Verificar Weston
docker logs weston

# Verificar dispositivos gráficos
ls -la /dev/dri/
ls -la /dev/galcore
```

#### Aplicação Não Aparece
```bash
# Verificar se Weston está rodando
docker ps | grep weston

# Verificar variáveis de ambiente
docker exec potato-identifier-gui env | grep DISPLAY
```

## 📷 Configuração de Câmera

### Dispositivos Suportados
- **USB Camera**: `/dev/video0`
- **CSI Camera**: Dependendo da configuração
- **Basler**: Via GigE ou USB3

### Verificação
```bash
# Listar câmeras disponíveis
v4l2-ctl --list-devices

# Testar câmera
ffmpeg -f v4l2 -i /dev/video0 -t 5 test.mp4
```

## 🔧 Configurações Avançadas

### Variáveis de Ambiente NPU
Definidas em `config/imx8mp-npu.env`:
```bash
CORAL_ENABLE_EDGETPU=1
NPU_AVAILABLE=1
VIPNPU_DEVICE=/dev/vipnpu
VIV_MGPU_KERNEL_CONFIG=1
```

### Otimizações de Performance
```bash
# Threads otimizadas para iMX8MP
OMP_NUM_THREADS=4
TF_NUM_INTEROP_THREADS=4
TF_NUM_INTRAOP_THREADS=4
```

### GPU Vivante
```bash
# Configurações específicas
VIV_MGPU_KERNEL_CONFIG=1
IMX_VPU_ENABLE_TILE_OPTIMIZE=1
```

## 📊 Monitoramento de Performance

### Métricas da Aplicação
Os logs incluem:
- Tempo de inferência (ms)
- Número de detecções por frame
- Status da NPU/CPU
- Taxa de FPS efetiva

### Exemplo de Log
```
INFO: 🧠 Modelo carregado com sucesso na NPU!
INFO: 📐 Input shape: [1, 416, 416, 3]
INFO: 🚀 Aceleração por NPU ativa!
INFO: Detectado: potato_good com confiança 0.95
INFO: ✅ Enviado para PLC: potato_good (1)
```

## 🛠️ Troubleshooting

### Problemas Comuns

#### 1. NPU Não Detectada
```bash
# Verificar drivers
lsmod | grep vipnpu
ls -la /dev/vipnpu*

# Fallback para CPU
export NPU_AVAILABLE=0
```

#### 2. Sem Interface Gráfica
```bash
# Forçar modo headless
export HEADLESS=1

# Verificar compositor
docker restart weston
```

#### 3. Performance Baixa
```bash
# Verificar se está usando NPU
docker logs potato-identifier-gui | grep NPU

# Verificar recursos do sistema
docker exec potato-identifier-gui top
```

#### 4. Câmera Não Funciona
```bash
# Verificar permissões
docker exec potato-identifier-gui ls -la /dev/video*

# Testar acesso
docker exec potato-identifier-gui v4l2-ctl --list-devices
```

## 📝 Próximos Passos

1. **Teste com câmera real** na Verdin iMX8MP
2. **Validação da NPU** com modelo EdgeTPU
3. **Otimização de performance** específica para iMX8MP  
4. **Configuração de PLC** via rede industrial
5. **Testes de estabilidade** de longa duração

---

**Nota**: Esta configuração foi otimizada especificamente para Toradex Verdin iMX8MP com Dahlia Carrier Board, aproveitando ao máximo os recursos de NPU e GPU disponíveis.
