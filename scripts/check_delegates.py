#!/usr/bin/env python3
"""
Script para verificar a disponibilidade de delegates de aceleração de hardware
na placa Toradex Verdin iMX8MP.

Este script ajuda a diagnosticar problemas com delegates NPU/GPU/VPU.
"""

import os
import sys
import subprocess
import logging

# Configuração do logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_file_exists(file_path, description):
    """Verifica se um arquivo existe e suas permissões."""
    if os.path.exists(file_path):
        stat_info = os.stat(file_path)
        size = stat_info.st_size
        permissions = oct(stat_info.st_mode)[-3:]
        logger.info(f"✅ {description}: {file_path} (tamanho: {size} bytes, permissões: {permissions})")
        return True
    else:
        logger.warning(f"❌ {description}: {file_path} - NÃO ENCONTRADO")
        return False

def check_system_info():
    """Verifica informações do sistema."""
    try:
        logger.info("=== INFORMAÇÕES DO SISTEMA ===")
        
        # Informações da CPU
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpu_info = f.read()
                if 'imx8mp' in cpu_info.lower():
                    logger.info("✅ Processador: iMX8MP detectado")
                elif 'imx8' in cpu_info.lower():
                    logger.info("✅ Processador: iMX8 família detectada")
                else:
                    logger.warning("⚠️  Processador iMX não claramente identificado")
        except:
            logger.error("❌ Não foi possível ler informações da CPU")
        
        # Kernel
        try:
            kernel_version = subprocess.check_output(['uname', '-r'], text=True).strip()
            logger.info(f"🐧 Kernel: {kernel_version}")
        except:
            logger.error("❌ Não foi possível obter versão do kernel")
            
        # Arquitetura
        try:
            arch = subprocess.check_output(['uname', '-m'], text=True).strip()
            logger.info(f"🏗️  Arquitetura: {arch}")
        except:
            logger.error("❌ Não foi possível obter arquitetura")
            
    except Exception as e:
        logger.error(f"Erro ao obter informações do sistema: {e}")

def check_delegates():
    """Verifica a disponibilidade de delegates de aceleração."""
    logger.info("\n=== VERIFICAÇÃO DE DELEGATES ===")
    
    # Delegates específicos para Torizon/iMX8MP
    delegates = [
        ("/usr/lib/libvx_delegate.so", "VX Delegate (GPU/VPU)"),
        ("/usr/lib/aarch64-linux-gnu/libvx_delegate.so", "VX Delegate ARM64"),
        ("/usr/lib/arm-linux-gnueabihf/libvx_delegate.so", "VX Delegate ARM32"),
        # Bibliotecas base que podem indicar suporte a aceleração
        ("/usr/lib/libGAL.so", "GAL Library (Vivante GPU)"),
        ("/usr/lib/aarch64-linux-gnu/libGAL.so", "GAL Library ARM64"),
        ("/usr/lib/libVSC.so", "VSC Library (Vivante)"),
        ("/usr/lib/aarch64-linux-gnu/libVSC.so", "VSC Library ARM64"),
        # NPU específicos (podem não estar presentes em todas as versões)
        ("/usr/lib/libimxnn_delegate.so", "iMX NN Delegate (NPU específico)"),
        ("/usr/lib/libethosu_delegate.so", "Ethos-U Delegate (NPU ARM)"),
        ("/usr/lib/libnnrt.so", "Neural Network Runtime"),
    ]
    
    found_delegates = 0
    for delegate_path, description in delegates:
        if check_file_exists(delegate_path, description):
            found_delegates += 1
    
    logger.info(f"\n📊 Total de delegates encontrados: {found_delegates}/{len(delegates)}")
    
    return found_delegates > 0

def check_tflite_installation():
    """Verifica a instalação do TensorFlow Lite."""
    logger.info("\n=== VERIFICAÇÃO DO TENSORFLOW LITE ===")
    
    try:
        import tflite_runtime.interpreter as tflite
        logger.info("✅ TensorFlow Lite Runtime importado com sucesso")
        
        # Verificar versão
        try:
            version = tflite.__version__
            logger.info(f"📦 Versão: {version}")
        except:
            logger.warning("⚠️  Não foi possível obter versão do TFLite")
            
        return True
    except ImportError as e:
        logger.error(f"❌ Erro ao importar TensorFlow Lite: {e}")
        return False

def check_opencv():
    """Verifica a instalação do OpenCV."""
    logger.info("\n=== VERIFICAÇÃO DO OPENCV ===")
    
    try:
        import cv2
        logger.info("✅ OpenCV importado com sucesso")
        logger.info(f"📦 Versão: {cv2.__version__}")
        
        # Verificar backends disponíveis
        backends = cv2.getBuildInformation()
        if 'gstreamer' in backends.lower():
            logger.info("✅ GStreamer suportado")
        if 'v4l' in backends.lower():
            logger.info("✅ Video4Linux suportado")
            
        return True
    except ImportError as e:
        logger.error(f"❌ Erro ao importar OpenCV: {e}")
        return False

def check_device_tree():
    """Verifica informações do Device Tree."""
    logger.info("\n=== VERIFICAÇÃO DO DEVICE TREE ===")
    
    dt_paths = [
        "/proc/device-tree/compatible",
        "/proc/device-tree/model",
        "/sys/firmware/devicetree/base/compatible"
    ]
    
    for dt_path in dt_paths:
        if os.path.exists(dt_path):
            try:
                with open(dt_path, 'rb') as f:
                    content = f.read().decode('utf-8', errors='ignore').strip('\x00')
                    if content:
                        logger.info(f"📋 {dt_path}: {content}")
            except Exception as e:
                logger.warning(f"Erro ao ler {dt_path}: {e}")

def test_delegate_loading():
    """Testa o carregamento dos delegates disponíveis."""
    logger.info("\n=== TESTE DE CARREGAMENTO DE DELEGATES ===")
    
    try:
        import tflite_runtime.interpreter as tflite
        
        delegates_to_test = [
            "/usr/lib/libvx_delegate.so",
            "/usr/lib/aarch64-linux-gnu/libvx_delegate.so",
            "/usr/lib/libimxnn_delegate.so",
            "/usr/lib/libethosu_delegate.so"
        ]
        
        working_delegates = []
        
        for delegate_path in delegates_to_test:
            if os.path.exists(delegate_path):
                try:
                    # Tentar carregar o delegate
                    delegate = tflite.load_delegate(delegate_path)
                    logger.info(f"✅ Delegate carregado com sucesso: {delegate_path}")
                    working_delegates.append(delegate_path)
                    
                    # Tentar criar um interpretador simples para testar
                    try:
                        # Criar um modelo simples para teste (apenas verificar se não falha)
                        test_model = create_minimal_tflite_model()
                        if test_model:
                            interpreter = tflite.Interpreter(
                                model_content=test_model,
                                experimental_delegates=[delegate]
                            )
                            interpreter.allocate_tensors()
                            logger.info(f"🚀 Delegate {delegate_path} funcionando corretamente")
                        else:
                            logger.warning(f"⚠️  Não foi possível criar modelo de teste para {delegate_path}")
                    except Exception as e:
                        logger.warning(f"⚠️  Delegate {delegate_path} carregou mas falhou no teste: {e}")
                        
                except Exception as e:
                    logger.error(f"❌ Erro ao carregar delegate {delegate_path}: {e}")
        
        if working_delegates:
            logger.info(f"📊 Total de delegates funcionais: {len(working_delegates)}")
        else:
            logger.warning("⚠️  Nenhum delegate funcional encontrado")
                    
    except Exception as e:
        logger.error(f"Erro durante teste de delegates: {e}")

def create_minimal_tflite_model():
    """Cria um modelo TFLite mínimo para teste."""
    try:
        # Modelo mínimo em formato TFLite (identidade simples)
        # Este é um modelo que apenas passa a entrada para a saída
        model_data = bytearray([
            0x18, 0x00, 0x00, 0x00, 0x54, 0x46, 0x4c, 0x33, 0x00, 0x00, 0x0e, 0x00,
            0x18, 0x00, 0x04, 0x00, 0x08, 0x00, 0x0c, 0x00, 0x10, 0x00, 0x14, 0x00,
            0x0e, 0x00, 0x00, 0x00, 0x03, 0x00, 0x00, 0x00, 0x18, 0x00, 0x00, 0x00,
            0x20, 0x00, 0x00, 0x00, 0x44, 0x00, 0x00, 0x00, 0x0c, 0x00, 0x14, 0x00,
            0x04, 0x00, 0x08, 0x00, 0x0c, 0x00, 0x10, 0x00, 0x0c, 0x00, 0x00, 0x00,
            0x2c, 0x00, 0x00, 0x00, 0x20, 0x00, 0x00, 0x00, 0x14, 0x00, 0x00, 0x00,
            0x04, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x01, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00,
            0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
        ])
        return bytes(model_data)
    except:
        return None

def main():
    """Função principal."""
    logger.info("🔍 VERIFICADOR DE DELEGATES TORADEX VERDIN iMX8MP")
    logger.info("=" * 60)
    
    # Verificações do sistema
    check_system_info()
    
    # Verificações de software
    tflite_ok = check_tflite_installation()
    opencv_ok = check_opencv()
    
    # Verificações de hardware/drivers
    check_device_tree()
    delegates_available = check_delegates()
    
    # Teste de carregamento
    if tflite_ok and delegates_available:
        test_delegate_loading()
    
    # Resumo final
    logger.info("\n" + "=" * 60)
    logger.info("📋 RESUMO FINAL")
    logger.info("=" * 60)
    
    if tflite_ok:
        logger.info("✅ TensorFlow Lite: OK")
    else:
        logger.error("❌ TensorFlow Lite: PROBLEMA")
        
    if opencv_ok:
        logger.info("✅ OpenCV: OK")
    else:
        logger.error("❌ OpenCV: PROBLEMA")
        
    if delegates_available:
        logger.info("✅ Delegates de Aceleração: DISPONÍVEIS")
        logger.info("💡 Sua aplicação deve conseguir usar aceleração de hardware!")
    else:
        logger.warning("⚠️  Delegates de Aceleração: NÃO ENCONTRADOS")
        logger.warning("💡 A aplicação funcionará apenas em CPU.")
        
    logger.info("\n🏁 Verificação concluída!")

if __name__ == "__main__":
    main()
