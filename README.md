# Potato Identifier - Sistema de Visão Computacional

Sistema de visão computacional para identificação de batatas e pedras usando TensorFlow Lite e NPU (Neural Processing Unit) em placas Toradex IMX8MP com board Dahlia.

## 🚀 Características

- ✅ Detecção de batatas (OK/NOK) e pedras usando modelo YOLOv8
- ✅ Suporte à NPU (EdgeTPU) para inferência acelerada
- ✅ Interface gráfica com Tkinter para visualização em tempo real
- ✅ Integração com PLC via protocolo Snap7
- ✅ Suporte à câmeras Basler via PyPylon
- ✅ Containerização com Docker para fácil deployment
- ✅ Ambiente de desenvolvimento local e produção

## 📋 Pré-requisitos

### Hardware
- Placa Toradex IMX8MP com board Dahlia
- Câmera Basler compatível com PyPylon
- PLC compatível com protocolo Snap7 (opcional)

### Software
- Docker e Docker Compose
- Python 3.8+ (para desenvolvimento local)

## 🛠️ Instalação e Configuração

### 1. Clone o repositório
```bash
git clone <repository-url>
cd potato-Identifier
```

### 2. Configure o ambiente de desenvolvimento
```bash
# Use o script de desenvolvimento para configuração automática
./scripts/dev.sh setup

# Ou configure manualmente:
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-local.txt
```

### 3. Verifique as dependências
```bash
./scripts/dev.sh check-deps
```

### 4. Verifique suporte à NPU (apenas na placa Toradex)
```bash
./scripts/dev.sh check-npu
```

## 🏃‍♂️ Execução

### Desenvolvimento Local
Para desenvolvimento e testes locais (sem câmera real):

```bash
# Executar com Docker
./scripts/dev.sh run-local

# Ou executar diretamente com Python
source .venv/bin/activate
python src/main.py
```

### Produção na Placa Toradex
Para executar na placa Toradex IMX8MP:

```bash
# Construir e executar imagem de produção
./scripts/dev.sh build-prod
./scripts/dev.sh run-prod

# Ou usar Docker Compose diretamente
docker-compose -f docker-compose.prod.yml up --build
```

## 📁 Estrutura do Projeto

```
potato-Identifier/
├── src/
│   ├── main.py              # Aplicação principal
│   ├── plc.py              # Interface com PLC
│   └── check_npu.py        # Verificação de suporte à NPU
├── data/
│   └── models/
│       ├── best_float32_edgetpu.tflite  # Modelo para NPU
│       ├── best_float32.tflite          # Modelo fallback
│       └── labels.txt                   # Classes do modelo
├── scripts/
│   └── dev.sh              # Script de desenvolvimento
├── docker-compose.yml      # Configuração para desenvolvimento
├── docker-compose.prod.yml # Configuração para produção
├── docker-compose.dev.yml  # Configuração para dev local
├── Dockerfile              # Imagem de produção (Toradex)
├── Dockerfile.local        # Imagem para desenvolvimento local
└── requirements-*.txt      # Dependências Python
```

## ⚙️ Configuração

### Configurações da Câmera
As configurações da câmera Basler podem ser ajustadas no arquivo `src/main.py`:

```python
# Configurar parâmetros da câmera
if self.camera.Width.IsWritable():
    self.camera.Width.SetValue(640)
if self.camera.Height.IsWritable():
    self.camera.Height.SetValue(480)
```

### Configurações do PLC
Ajuste o endereço IP do PLC no arquivo `src/plc.py`:

```python
self.client.connect("192.168.2.201", 0, 1)  # IP, rack, slot
```

### Configurações do Docker
Ajuste as configurações da placa no arquivo `.vscode/settings.json`:

```json
{
    "torizon_ip": "192.168.100.174",
    "host_ip": "192.168.100.146",
    "torizon_arch": "aarch64",
    "torizon_gpu": "-imx8"
}
```

## 🧪 Testes

### Testar Conexão com PLC
```bash
./scripts/dev.sh test-plc
```

### Testar NPU
```bash
./scripts/dev.sh check-npu
```

### Ver Logs
```bash
./scripts/dev.sh logs
```

## 🔧 Desenvolvimento

### Script de Desenvolvimento
O script `./scripts/dev.sh` oferece várias funcionalidades:

```bash
./scripts/dev.sh help           # Mostra ajuda
./scripts/dev.sh setup          # Configura ambiente
./scripts/dev.sh check-deps     # Verifica dependências
./scripts/dev.sh check-npu      # Verifica NPU
./scripts/dev.sh build-local    # Constrói imagem local
./scripts/dev.sh build-prod     # Constrói imagem produção
./scripts/dev.sh run-local      # Executa localmente
./scripts/dev.sh run-prod       # Executa na placa
./scripts/dev.sh test-plc       # Testa PLC
./scripts/dev.sh logs           # Mostra logs
./scripts/dev.sh clean          # Limpa ambiente
```

### Desenvolvimento com Hot Reload
Para desenvolvimento com recarga automática:

```bash
# O docker-compose.dev.yml monta o diretório src como volume
docker-compose -f docker-compose.dev.yml up --build
```

## 🏗️ Build e Deploy

### Build Local
```bash
docker-compose -f docker-compose.dev.yml build
```

### Build para Produção
```bash
docker-compose -f docker-compose.yml build
```

### Deploy na Placa Toradex
1. Configure o IP da placa em `.vscode/settings.json`
2. Execute: `./scripts/dev.sh run-prod`

## 📊 Monitoramento

A aplicação exibe informações em tempo real:
- Tempo de inferência (ms)
- Número de detecções
- Confiança das predições
- Status da conexão PLC

## 🐛 Troubleshooting

### Problema: Câmera não detectada
- Verifique se a câmera está conectada
- Verifique se os drivers PyPylon estão instalados
- Verifique se o container tem acesso aos dispositivos USB

### Problema: NPU não funciona
- Verifique se `libedgetpu.so.1` está disponível
- Execute `./scripts/dev.sh check-npu` para diagnóstico
- Verifique se o modelo EdgeTPU está no diretório correto

### Problema: PLC não conecta
- Verifique o IP do PLC em `src/plc.py`
- Teste a conectividade de rede
- Execute `./scripts/dev.sh test-plc`

## 📝 Logs

Os logs são salvos com diferentes níveis:
- INFO: Informações gerais
- WARNING: Avisos (câmera, PLC, etc.)
- ERROR: Erros recuperáveis
- CRITICAL: Erros fatais

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

## 📞 Suporte

Para suporte técnico, abra uma issue no repositório ou contate a equipe de desenvolvimento.
