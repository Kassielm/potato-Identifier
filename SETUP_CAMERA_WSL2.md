# Configuração da Câmera Basler no WSL2

## Problema
O WSL2 não tem acesso direto aos dispositivos USB do Windows. Para usar a câmera Basler no WSL2, precisamos configurar o compartilhamento USB.

## Solução: USB/IP com usbipd-win

### 1. Instalar usbipd-win no Windows

1. Abra o PowerShell como **Administrador**
2. Execute:
```powershell
winget install --interactive --exact dorssel.usbipd-win
```

Ou baixe diretamente do [GitHub](https://github.com/dorssel/usbipd-win/releases)

### 2. Configurar usbipd no Windows

1. **Reinicie o Windows** após a instalação
2. Abra PowerShell como **Administrador**
3. Liste os dispositivos USB:
```powershell
usbipd list
```

Procure pela sua câmera Basler (algo como "Basler" ou com VID similar)

### 3. Compartilhar a Câmera

No PowerShell (como Administrador):

```powershell
# Substitua X-Y pelo BUSID da sua câmera
usbipd bind --busid X-Y

# Depois compartilhe com o WSL2
usbipd attach --wsl --busid X-Y
```

### 4. Verificar no WSL2

No terminal WSL2:
```bash
# Verificar se a câmera aparece
lsusb

# Verificar dispositivos de vídeo
ls -la /dev/video*

# Verificar permissões USB
ls -la /dev/bus/usb/
```

### 5. Script Automático de Configuração

Criei um script para facilitar a configuração:

```bash
# No WSL2, execute:
./scripts/dev.sh setup-camera
```

## Alternativas

### Opção 1: Docker Desktop com Suporte USB
Se você tem Docker Desktop, pode usar volumes para mapear dispositivos.

### Opção 2: Aplicação Híbrida
- Interface no Windows (acesso direto à câmera)
- Processamento ML no WSL2 via API/Socket

### Opção 3: Desenvolvimento Direto no Windows
- Instalar Python no Windows
- Usar PyPylon diretamente
- Docker Desktop para containers

## Comandos PowerShell de Referência

```powershell
# Listar dispositivos
usbipd list

# Bind device (uma vez só)
usbipd bind --busid 1-2

# Attach ao WSL2
usbipd attach --wsl --busid 1-2

# Detach do WSL2
usbipd detach --busid 1-2

# Status
usbipd state
```

## Comandos WSL2 de Referência

```bash
# Verificar USB
lsusb

# Verificar dispositivos de vídeo
ls /dev/video*

# Testar câmera com PyPylon
python -c "from pypylon import pylon; print(f'Câmeras: {pylon.TlFactory.GetInstance().EnumerateDevices()}')"

# Permissões USB (se necessário)
sudo chmod 666 /dev/bus/usb/*/*
```

## Solução de Problemas

### Câmera não aparece no lsusb
1. Verifique se fez bind no Windows
2. Verifique se fez attach ao WSL2
3. Reinicie o WSL2: `wsl --shutdown` e reabra

### Erro de permissão
```bash
# Adicionar usuário ao grupo dialout
sudo usermod -a -G dialout $USER

# Reiniciar WSL2
exit
# Reabrir WSL2
```

### PyPylon não encontra câmera
```bash
# Verificar variáveis de ambiente
export PYLON_ROOT=/usr/local
export GENICAM_GENTL64_PATH=/usr/local/lib

# Instalar drivers adicionais
sudo apt install -y libusb-1.0-0-dev
```

## Teste Final

Execute o script de teste:
```bash
cd /home/cristiano/potato-Identifier
./scripts/dev.sh test-camera
```
