#!/usr/bin/env python3
"""
Script para verificar a disponibilidade da NPU (EdgeTPU) na placa Toradex IMX8MP
"""

import os
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_edgetpu_library():
    """Verifica se a biblioteca EdgeTPU está disponível"""
    try:
        # Tenta importar tflite_runtime primeiro, depois tensorflow.lite como fallback
        try:
            import tflite_runtime.interpreter as tflite
            using_tflite_runtime = True
            logger.info("✓ TFLite Runtime disponível")
        except ImportError:
            import tensorflow as tf_full
            tflite = tf_full.lite
            using_tflite_runtime = False
            logger.info("✓ TensorFlow Lite (via TensorFlow completo) disponível")
        
        # Verifica se o delegate EdgeTPU está disponível
        if using_tflite_runtime:
            try:
                delegate = tflite.load_delegate('libedgetpu.so.1')
                logger.info("✓ EdgeTPU delegate (libedgetpu.so.1) disponível")
                return True
            except Exception as e:
                logger.warning(f"✗ EdgeTPU delegate não disponível: {e}")
                
                # Tenta outros caminhos possíveis
                possible_paths = [
                    'libedgetpu.so',
                    '/usr/lib/libedgetpu.so.1',
                    '/usr/lib/aarch64-linux-gnu/libedgetpu.so.1'
                ]
                
                for path in possible_paths:
                    try:
                        delegate = tflite.load_delegate(path)
                        logger.info(f"✓ EdgeTPU delegate encontrado em: {path}")
                        return True
                    except Exception:
                        continue
                        
                logger.error("✗ Nenhum EdgeTPU delegate encontrado")
                return False
        else:
            logger.info("ℹ  Usando TensorFlow completo - EdgeTPU delegate não aplicável")
            return True
            
    except ImportError as e:
        logger.error(f"✗ Nem TFLite Runtime nem TensorFlow disponível: {e}")
        return False

def check_device_files():
    """Verifica se os arquivos de dispositivo necessários estão presentes"""
    device_files = [
        '/dev/galcore',
        '/dev/dri',
        '/sys/devices'
    ]
    
    for device in device_files:
        if os.path.exists(device):
            logger.info(f"✓ Device file disponível: {device}")
        else:
            logger.warning(f"✗ Device file não encontrado: {device}")

def check_models():
    """Verifica se os modelos estão disponíveis"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    models_dir = os.path.join(base_dir, 'data', 'models')
    
    models = [
        'best_float32_edgetpu.tflite',
        'best_float32.tflite',
        'labels.txt'
    ]
    
    for model in models:
        model_path = os.path.join(models_dir, model)
        if os.path.exists(model_path):
            logger.info(f"✓ Modelo disponível: {model}")
        else:
            logger.warning(f"✗ Modelo não encontrado: {model}")

def main():
    logger.info("=== Verificação do Sistema NPU/EdgeTPU ===")
    
    logger.info("\n1. Verificando biblioteca EdgeTPU...")
    edgetpu_available = check_edgetpu_library()
    
    logger.info("\n2. Verificando arquivos de dispositivo...")
    check_device_files()
    
    logger.info("\n3. Verificando modelos...")
    check_models()
    
    logger.info("\n=== Resumo ===")
    if edgetpu_available:
        logger.info("✓ Sistema pronto para usar NPU/EdgeTPU")
        return 0
    else:
        logger.error("✗ Sistema não está configurado para NPU/EdgeTPU")
        logger.info("A aplicação funcionará apenas com CPU")
        return 1

if __name__ == "__main__":
    sys.exit(main())
