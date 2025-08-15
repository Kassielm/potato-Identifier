#!/usr/bin/env python3
"""
Script de diagnóstico para verificar delegates TensorFlow Lite
"""

import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_delegate_files():
    """Verificar se arquivos de delegate existem"""
    delegate_paths = [
        '/usr/lib/libvx_delegate.so',
        '/usr/local/lib/libvx_delegate.so',
        '/usr/lib/aarch64-linux-gnu/libvx_delegate.so',
        '/usr/lib/arm-linux-gnueabihf/libvx_delegate.so'
    ]
    
    logger.info("🔍 Verificando arquivos de delegate...")
    found = False
    
    for path in delegate_paths:
        if os.path.exists(path):
            logger.info(f"✅ Encontrado: {path}")
            found = True
        else:
            logger.info(f"❌ Não encontrado: {path}")
    
    return found

def test_tflite_import():
    """Testar importação do TensorFlow Lite"""
    try:
        import tflite_runtime.interpreter as tflite
        logger.info("✅ tflite_runtime importado com sucesso")
        return tflite, True
    except ImportError:
        try:
            import tensorflow as tf
            logger.info("✅ tensorflow importado com sucesso")
            return tf.lite, False
        except ImportError:
            logger.error("❌ Nenhuma biblioteca TensorFlow disponível")
            return None, False

def test_delegate_loading(tflite_module, using_runtime):
    """Testar carregamento de delegate"""
    delegate_paths = [
        '/usr/lib/libvx_delegate.so',
        '/usr/local/lib/libvx_delegate.so'
    ]
    
    for delegate_path in delegate_paths:
        if os.path.exists(delegate_path):
            try:
                logger.info(f"🧪 Testando carregamento: {delegate_path}")
                
                if using_runtime:
                    delegate = tflite_module.load_delegate(delegate_path)
                else:
                    delegate = tflite_module.experimental.load_delegate(delegate_path)
                    
                logger.info(f"✅ Delegate carregado: {delegate_path}")
                return True
                
            except Exception as e:
                logger.error(f"❌ Erro ao carregar {delegate_path}: {e}")
                
    return False

def check_npu_device():
    """Verificar se dispositivo NPU está disponível"""
    npu_paths = [
        '/dev/galcore',
        '/sys/class/misc/galcore',
        '/proc/device-tree/soc@0/npu@38500000'
    ]
    
    logger.info("🔍 Verificando dispositivos NPU...")
    found = False
    
    for path in npu_paths:
        if os.path.exists(path):
            logger.info(f"✅ NPU device encontrado: {path}")
            found = True
        else:
            logger.info(f"❌ NPU device não encontrado: {path}")
    
    return found

def main():
    logger.info("========================================")
    logger.info("    Diagnóstico de Delegates TFLite")
    logger.info("========================================")
    
    # 1. Verificar arquivos de delegate
    delegate_files_found = check_delegate_files()
    
    # 2. Testar importação TensorFlow Lite
    tflite_module, using_runtime = test_tflite_import()
    
    if not tflite_module:
        logger.error("❌ Não é possível continuar sem TensorFlow Lite")
        return
    
    # 3. Testar carregamento de delegate
    if delegate_files_found:
        delegate_loaded = test_delegate_loading(tflite_module, using_runtime)
    else:
        delegate_loaded = False
    
    # 4. Verificar dispositivos NPU
    npu_device_found = check_npu_device()
    
    # 5. Resumo
    logger.info("\n========================================")
    logger.info("             RESUMO")
    logger.info("========================================")
    logger.info(f"Arquivos de delegate encontrados: {'✅' if delegate_files_found else '❌'}")
    logger.info(f"Delegate carregado com sucesso: {'✅' if delegate_loaded else '❌'}")
    logger.info(f"Dispositivo NPU encontrado: {'✅' if npu_device_found else '❌'}")
    
    if delegate_loaded and npu_device_found:
        logger.info("🎉 Sistema pronto para usar NPU!")
    elif delegate_files_found and not delegate_loaded:
        logger.warning("⚠️ Delegate disponível mas não carrega - possível incompatibilidade")
    else:
        logger.info("ℹ️ Sistema funcionará em modo CPU")

if __name__ == "__main__":
    main()
