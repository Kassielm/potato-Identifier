# Potato Identifier - Aplicação Torizon

## Descrição
Aplicação de visão computacional para identificação de batatas e pedras usando TensorFlow Lite com suporte à NPU (Neural Processing Unit) da placa Toradex IMX8MP e board Dhalia.

## Características Principais

### 🧠 Inteligência Artificial
- **TensorFlow Lite** com delegado EdgeTPU para NPU
- **Fallback automático** para CPU quando NPU não disponível
- **Modelo otimizado** para detecção de objetos (batatas vs pedras)
- **Classes**: OK, NOK, PEDRA

### 📷 Visão Computacional
- **OpenCV 4.8.1** para processamento de imagem
- **PyPylon** para câmeras Basler
- **Interface gráfica** com Tkinter
- **Exibição em tempo real** das inferências

### 🔗 Comunicação PLC
- **Snap7** para protocolo S7
- **Reconexão automática** em caso de falha
- **Logging detalhado** de operações

### 🐳 Containerização
- **Docker multi-arquitetura** (AMD64 para desenvolvimento, ARM64 para produção)
- **Ambiente isolado** para desenvolvimento
- **Configuração automática** para Torizon OS

## Estrutura do Projeto

```
potato-Identifier/
├── src/
│   ├── main.py              # Aplicação principal
│   ├── plc.py               # Comunicação PLC
│   ├── check_npu.py         # Verificação NPU/EdgeTPU
│   └── test_system.py       # Testes do sistema
├── data/
│   └── models/
│       ├── best_float32_edgetpu.tflite  # Modelo NPU
│       ├── best_float32.tflite          # Modelo CPU
│       ├── best-v3.pt                   # Modelo original
│       └── labels.txt                   # Classes
├── scripts/
│   └── dev.sh               # Script de desenvolvimento
├── Dockerfile.dev           # Docker para desenvolvimento
├── Dockerfile               # Docker para produção
├── docker-compose.yml       # Orquestração local
├── docker-compose.prod.yml  # Orquestração produção
└── requirements-*.txt       # Dependências
```

## Configuração de Desenvolvimento

### Pré-requisitos
- Docker
- Python 3.11+
- VS Code (opcional)

### Comandos Disponíveis

```bash
# Build da imagem de desenvolvimento
./scripts/dev.sh build

# Execução da aplicação
./scripts/dev.sh run

# Testes do sistema
./scripts/dev.sh test

# Verificação NPU
./scripts/dev.sh check-npu
```

### Ambiente Local (sem Docker)

```bash
# Criar ambiente virtual
python3 -m venv .venv
source .venv/bin/activate

# Instalar dependências
pip install -r requirements-local.txt

# Executar aplicação
python src/main.py
```

## Configuração de Produção (Torizon)

### Hardware Suportado
- **Toradex Verdin IMX8M Plus** com NPU
- **Board Dahlia** como carrier board
- **Câmera Basler** compatível com PyPylon

### Deploy

```bash
# Build imagem de produção
docker build -f Dockerfile -t potato-identifier:prod .

# Executar no Torizon
docker-compose -f docker-compose.prod.yml up
```

## Funcionalidades Técnicas

### Sistema de NPU
- **Detecção automática** da disponibilidade do EdgeTPU
- **Fallback inteligente** para CPU em caso de indisponibilidade
- **Logs detalhados** sobre o delegado utilizado

### Tratamento de Erros
- **Reconexão automática** para câmera e PLC
- **Logging estruturado** para debug
- **Graceful shutdown** em caso de falha

### Performance
- **Otimização para ARM64** (produção)
- **Compatibilidade AMD64** (desenvolvimento)
- **Uso eficiente de memória**

## Dependências Principais

| Biblioteca | Versão | Propósito |
|------------|--------|-----------|
| tensorflow | >=2.15.0 | IA/ML (desenvolvimento) |
| tflite-runtime | 2.14.0 | IA/ML (produção) |
| opencv-python | 4.8.1.78 | Visão computacional |
| pypylon | 4.2.0 | Interface câmera Basler |
| python-snap7 | 2.0.2 | Comunicação PLC |
| Pillow | >=10.0.0 | Processamento de imagem |
| numpy | <2.0 | Computação numérica |

## Logs e Debugging

### Níveis de Log
- **INFO**: Operações normais
- **WARNING**: Situações de atenção
- **ERROR**: Falhas recuperáveis
- **CRITICAL**: Falhas não recuperáveis

### Arquivos de Log
- Console output para desenvolvimento
- Syslog integration para produção

## Solução de Problemas

### NPU não detectada
```bash
# Verificar disponibilidade
./scripts/dev.sh check-npu

# Logs esperados
INFO - NPU/EdgeTPU não detectada, usando CPU
```

### Câmera não encontrada
```bash
# Verificar conexão física
# Logs esperados
ERROR - Nenhuma câmera Pylon encontrada!
```

### PLC desconectado
```bash
# Logs esperados
WARNING - Falha na conexão PLC, tentando reconectar...
```

## Desenvolvimento Futuro

### Melhorias Planejadas
- [ ] Suporte a múltiplas câmeras
- [ ] Interface web para monitoramento
- [ ] Métricas de performance
- [ ] Configuração via arquivo

### Otimizações
- [ ] Quantização INT8 para melhor performance NPU
- [ ] Cache de modelos
- [ ] Processamento em lote

## Contribuição
Para contribuir com o projeto, siga as diretrizes:
1. Fork do repositório
2. Criação de branch feature
3. Testes unitários
4. Pull request com descrição detalhada

## Licença
Propriedade da empresa. Uso interno apenas.

---

**Última atualização**: 13/08/2025
**Versão**: 1.0.0
**Compatibilidade**: Torizon OS 6.x, Python 3.11+
