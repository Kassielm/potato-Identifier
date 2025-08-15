# Modo Headless - Potato Identifier

## 🎯 Objetivo
Permitir que a aplicação Potato Identifier execute em ambientes sem interface gráfica (headless), como na placa Torizon ARM64, mantendo toda a funcionalidade de visão computacional e comunicação PLC.

## 🔧 Implementação

### Detecção Automática
A aplicação detecta automaticamente o modo headless através de:
- **Variável de ambiente**: `HEADLESS=1`
- **Ausência de DISPLAY**: Quando `$DISPLAY` não está definido
- **Fallback por importação**: Se tkinter não estiver disponível

### Modificações Realizadas

#### 1. **src/main.py** - Importações Condicionais
```python
# Configuração do modo headless
HEADLESS_MODE = os.getenv('HEADLESS', '0') == '1' or os.getenv('DISPLAY') is None

# Importações condicionais para GUI
if not HEADLESS_MODE:
    try:
        import tkinter as tk
        from PIL import Image, ImageTk
    except ImportError as e:
        print(f"Aviso: Bibliotecas GUI não disponíveis: {e}")
        print("Executando em modo headless...")
        HEADLESS_MODE = True
```

#### 2. **VisionSystem Class** - Construtor Flexível
```python
def __init__(self, root=None):
    self.root = root
    self.headless = HEADLESS_MODE or root is None
    
    if not self.headless:
        self.root.title("Vision System")
        self.canvas = tk.Canvas(root, width=640, height=480)
        self.canvas.pack()
```

#### 3. **Process Frame** - Exibição Condicional
```python
# --- Lógica de Exibição com Tkinter (apenas em modo GUI) ---
if not self.headless:
    # Código do tkinter...
    img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    imgtk = ImageTk.PhotoImage(image=img)
    self.canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
```

#### 4. **Agendamento de Frames** - Threading vs Tkinter
```python
def _schedule_next_frame(self, delay_ms=10):
    """Agenda a próxima execução do process_frame, com suporte para modo headless"""
    if self.headless:
        # Em modo headless, usa threading.Timer
        import threading
        timer = threading.Timer(delay_ms / 1000.0, self.process_frame)
        timer.daemon = True
        timer.start()
    else:
        # Em modo GUI, usa tkinter.after
        self.root.after(delay_ms, self.process_frame)
```

#### 5. **Main Loop** - Execução Diferenciada
```python
if HEADLESS_MODE:
    logger.info("Modo HEADLESS detectado - iniciando sem interface gráfica")
    app = VisionSystem(root=None)
    app.start()
else:
    logger.info("Modo GUI - iniciando com interface gráfica")
    root = tk.Tk()
    app = VisionSystem(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.start()
    root.mainloop()
```

#### 6. **scripts/dev.sh** - Deploy com Headless
```bash
deploy_remote() {
    docker run -d \
        --name potato-identifier \
        --privileged \
        -v /dev:/dev \
        -e HEADLESS=1 \    # ← Força modo headless
        --restart unless-stopped \
        potato-identifier:latest
}
```

## 🚀 Como Usar

### Localmente (com GUI)
```bash
# Modo normal com interface gráfica
python src/main.py
```

### Localmente (modo headless)
```bash
# Forçar modo headless
HEADLESS=1 python src/main.py
```

### Deploy Remoto na Placa
```bash
# Usar o script dev.sh
./scripts/dev.sh deploy
```

## 📊 Funcionalidades Mantidas em Modo Headless

✅ **Inferência de IA**: Processamento completo com TensorFlow Lite
✅ **Comunicação PLC**: Envio de dados via snap7 com reconexão automática  
✅ **Logs detalhados**: Todas as detecções são registradas
✅ **Gestão de câmera**: Suporte USB e Basler
✅ **Robustez**: Reconexão automática de PLC e câmera
✅ **Performance**: Métricas de tempo de inferência

❌ **Interface visual**: Não há exibição de vídeo (por design)

## 🔍 Logs e Monitoramento

Em modo headless, toda informação é disponibilizada via logs:

```bash
# Ver logs em tempo real
docker logs -f potato-identifier

# Logs incluem:
# - Detecções realizadas
# - Confiança das predições  
# - Status de comunicação PLC
# - Tempo de inferência
# - Erros e reconexões
```

## 🛠️ Troubleshooting

### Problema: "No module named 'tkinter'"
**Solução**: A aplicação automaticamente detecta e ativa modo headless

### Problema: "no display name and no $DISPLAY environment variable"
**Solução**: Definir `HEADLESS=1` ou `unset DISPLAY`

### Problema: Container não acessa câmera
**Solução**: Usar `--privileged` e `-v /dev:/dev` no Docker

### Problema: PLC não conecta
**Solução**: Verificar IP e aguardar reconexão automática (logs mostrarão tentativas)

## 📈 Status da Implementação

- ✅ **Modo headless implementado**
- ✅ **Deploy remoto configurado** 
- ✅ **Fallback automático funcionando**
- ✅ **Logs detalhados ativos**
- 🔄 **Aguardando teste com hardware real** (câmera + PLC)

---

**Nota**: Esta implementação permite que o sistema funcione tanto em desenvolvimento (com GUI) quanto em produção (headless) sem modificações no código.
