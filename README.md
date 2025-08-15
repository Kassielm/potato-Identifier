# Potato Identifier - Sistema de Visão Computacional

Sistema de visão computacional para identificação de batatas e pedras usando TensorFlow Lite e NPU em placas Toradex Verdin IMX8MP com board Dahlia.

## 🚀 Características

- ✅ Detecção de batatas (OK/NOK) e pedras usando modelo YOLOv8
- ✅ Suporte à NPU (EdgeTPU) para inferência acelerada na Toradex
- ✅ Interface gráfica com OpenCV para visualização em tempo real
- ✅ Integração com PLC via protocolo Snap7
- ✅ Suporte à câmeras Basler via PyPylon
- ✅ Containerização com Docker para deployment

## 📋 Pré-requisitos

### Hardware
- Placa Toradex Verdin IMX8MP com board Dahlia
- Câmera Basler compatível com PyPylon
- PLC compatível com protocolo Snap7 (opcional)

### Software
- Docker e Docker Compose
- Python 3.8+ (para desenvolvimento local)

## 🛠️ Instalação Rápida

### 1. Configure o ambiente
```bash
git clone <repository-url>
cd potato-Identifier
./scripts/dev.sh setup
```

### 2. Teste o sistema
```bash
./scripts/dev.sh test
```

### 3. Execute localmente
```bash
./scripts/dev.sh run
```

### 4. Para produção na Toradex
```bash
./scripts/dev.sh build
./scripts/dev.sh run
```

## 📁 Estrutura Simplificada

```
potato-Identifier/
├── src/
│   ├── main.py              # Aplicação principal
│   ├── plc.py              # Interface com PLC
│   ├── check_npu.py        # Verificação de NPU
│   └── test_system.py      # Teste do sistema
├── data/models/            # Modelos TFLite
├── scripts/dev.sh          # Script de desenvolvimento
├── Dockerfile              # Imagem Docker
├── docker-compose.yml      # Configuração Docker
└── requirements-*.txt      # Dependências Python
```

## ⚙️ Configuração

### PLC
Ajuste o IP do PLC em `src/plc.py`:
```python
self.client.connect("192.168.2.201", 0, 1)  # IP, rack, slot
```

### Toradex
Ajuste as configurações em `.vscode/settings.json`:
```json
{
    "torizon_ip": "192.168.100.174",
    "host_ip": "192.168.100.146"
}
```

## 🧪 Comandos Disponíveis

```bash
./scripts/dev.sh setup    # Configura ambiente
./scripts/dev.sh check    # Verifica sistema
./scripts/dev.sh build    # Constrói imagem Docker
./scripts/dev.sh run      # Executa aplicação
./scripts/dev.sh test     # Testa sistema local
./scripts/dev.sh clean    # Limpa ambiente
```

## 🐛 Solução de Problemas

### Câmera não detectada
- Verifique conexão da câmera
- Verifique se PyPylon está instalado

### NPU não funciona
- Execute `./scripts/dev.sh check` para diagnóstico
- Verifique se está executando na placa Toradex

### PLC não conecta
- Verifique IP do PLC em `src/plc.py`
- Teste conectividade de rede

## 📄 Licença

Este projeto está sob a licença MIT.
