#!/usr/bin/env python3
"""
Script de diagnóstico para câmera Basler no WSL2
"""

import sys
import os
import subprocess
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def run_command(cmd):
    """Executa comando e retorna resultado"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_usb_devices():
    """Verifica dispositivos USB disponíveis"""
    logging.info("=== VERIFICAÇÃO USB ===")
    
    success, stdout, stderr = run_command("lsusb")
    if success:
        logging.info("Dispositivos USB encontrados:")
        for line in stdout.strip().split('\n'):
            if line.strip():
                logging.info(f"  {line}")
        
        # Procurar por dispositivos Basler
        basler_devices = [line for line in stdout.split('\n') if 'basler' in line.lower()]
        if basler_devices:
            logging.info("✅ Dispositivos Basler encontrados!")
            return True
        else:
            logging.warning("❌ Nenhum dispositivo Basler encontrado no USB")
            return False
    else:
        logging.error(f"Erro ao executar lsusb: {stderr}")
        return False

def check_video_devices():
    """Verifica dispositivos de vídeo"""
    logging.info("=== VERIFICAÇÃO DISPOSITIVOS DE VÍDEO ===")
    
    video_devices = []
    for i in range(10):  # Verificar /dev/video2 até /dev/video9
        device_path = f"/dev/video{i}"
        if os.path.exists(device_path):
            video_devices.append(device_path)
    
    if video_devices:
        logging.info("Dispositivos de vídeo encontrados:")
        for device in video_devices:
            logging.info(f"  {device}")
        return True
    else:
        logging.warning("❌ Nenhum dispositivo /dev/video* encontrado")
        return False

def check_pypylon():
    """Verifica PyPylon e câmeras Basler"""
    logging.info("=== VERIFICAÇÃO PYPYLON ===")
    
    try:
        from pypylon import pylon
        logging.info("✅ PyPylon importado com sucesso")
        
        # Enumerar dispositivos
        tlFactory = pylon.TlFactory.GetInstance()
        devices = tlFactory.EnumerateDevices()
        
        logging.info(f"Número de câmeras Basler encontradas: {len(devices)}")
        
        if len(devices) > 0:
            for i, device in enumerate(devices):
                logging.info(f"Câmera {i+1}:")
                logging.info(f"  - Nome: {device.GetFriendlyName()}")
                logging.info(f"  - Serial: {device.GetSerialNumber()}")
                logging.info(f"  - Modelo: {device.GetModelName()}")
            return True
        else:
            logging.warning("❌ Nenhuma câmera Basler detectada pelo PyPylon")
            return False
            
    except ImportError:
        logging.error("❌ PyPylon não está instalado")
        logging.info("💡 Execute: pip install pypylon")
        return False
    except Exception as e:
        logging.error(f"❌ Erro ao verificar PyPylon: {e}")
        return False

def check_permissions():
    """Verifica permissões USB"""
    logging.info("=== VERIFICAÇÃO PERMISSÕES ===")
    
    # Verificar se usuário está no grupo dialout
    success, stdout, stderr = run_command("groups")
    if success:
        groups = stdout.strip().split()
        if 'dialout' in groups:
            logging.info("✅ Usuário está no grupo dialout")
        else:
            logging.warning("❌ Usuário não está no grupo dialout")
            logging.info("💡 Execute: sudo usermod -a -G dialout $USER")
            logging.info("💡 Depois reinicie o WSL2")
    
    # Verificar estrutura USB
    if os.path.exists("/dev/bus/usb"):
        logging.info("✅ Estrutura /dev/bus/usb existe")
        
        # Verificar permissões
        success, stdout, stderr = run_command("ls -la /dev/bus/usb/")
        if success:
            logging.info("Estrutura USB:")
            for line in stdout.strip().split('\n')[:5]:  # Mostrar apenas primeiras linhas
                logging.info(f"  {line}")
    else:
        logging.warning("❌ Estrutura /dev/bus/usb não existe")

def print_instructions():
    """Imprime instruções para configuração"""
    logging.info("=== INSTRUÇÕES DE CONFIGURAÇÃO ===")
    logging.info("")
    logging.info("WINDOWS (PowerShell como Administrador):")
    logging.info("1. winget install --interactive --exact dorssel.usbipd-win")
    logging.info("2. Reiniciar Windows")
    logging.info("3. usbipd list")
    logging.info("4. usbipd bind --busid X-Y")
    logging.info("5. usbipd attach --wsl --busid X-Y")
    logging.info("")
    logging.info("WSL2:")
    logging.info("1. ./scripts/dev.sh test-camera")
    logging.info("2. ./scripts/dev.sh run")
    logging.info("")
    logging.info("Para mais detalhes: cat SETUP_CAMERA_WSL2.md")

def main():
    """Função principal"""
    logging.info("=== DIAGNÓSTICO CÂMERA BASLER WSL2 ===")
    logging.info("")
    
    results = {
        'usb': check_usb_devices(),
        'video': check_video_devices(),
        'pypylon': check_pypylon(),
        'permissions': True  # check_permissions não retorna boolean
    }
    
    check_permissions()
    
    logging.info("")
    logging.info("=== RESUMO ===")
    
    if results['pypylon']:
        logging.info("🎉 CÂMERA CONFIGURADA COM SUCESSO!")
        logging.info("✅ Pode executar a aplicação: ./scripts/dev.sh run")
    elif results['usb']:
        logging.info("🔄 CÂMERA DETECTADA MAS NÃO CONFIGURADA")
        logging.info("💡 Verifique drivers PyPylon ou permissões")
    else:
        logging.info("❌ CÂMERA NÃO DETECTADA")
        logging.info("💡 Configure usbipd no Windows conforme instruções")
        print_instructions()

if __name__ == "__main__":
    main()
