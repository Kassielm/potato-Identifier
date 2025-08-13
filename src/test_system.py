#!/usr/bin/env python3
"""
Teste básico para verificar se todas as importações estão funcionando
"""

import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_imports():
    """Testa todas as importações necessárias"""
    errors = []
    
    # Teste TensorFlow/TensorFlow Lite
    try:
        try:
            import tflite_runtime.interpreter as tf
            logger.info("✓ TFLite Runtime importado com sucesso")
            runtime_type = "TFLite Runtime"
        except ImportError:
            import tensorflow as tf_full
            tf = tf_full.lite
            logger.info("✓ TensorFlow Lite (via TensorFlow) importado com sucesso")
            runtime_type = "TensorFlow Lite"
    except ImportError as e:
        errors.append(f"TensorFlow/TFLite: {e}")
    
    # Teste NumPy
    try:
        import numpy as np
        logger.info(f"✓ NumPy {np.__version__} importado com sucesso")
    except ImportError as e:
        errors.append(f"NumPy: {e}")
    
    # Teste OpenCV
    try:
        import cv2
        logger.info(f"✓ OpenCV {cv2.__version__} importado com sucesso")
    except ImportError as e:
        errors.append(f"OpenCV: {e}")
    
    # Teste Pillow
    try:
        from PIL import Image, ImageTk
        import PIL
        logger.info(f"✓ Pillow {PIL.__version__} importado com sucesso")
    except ImportError as e:
        errors.append(f"Pillow: {e}")
    
    # Teste Snap7 (PLC)
    try:
        import snap7
        logger.info("✓ Snap7 importado com sucesso")
    except ImportError as e:
        errors.append(f"Snap7: {e}")
    
    # Teste Tkinter
    try:
        import tkinter as tk
        logger.info("✓ Tkinter importado com sucesso")
    except ImportError as e:
        errors.append(f"Tkinter: {e}")
    
    return errors

def test_model_loading():
    """Testa o carregamento do modelo"""
    import os
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    
    models = [
        'data/models/best_float32_edgetpu.tflite',
        'data/models/best_float32.tflite',
        'data/models/labels.txt'
    ]
    
    missing_models = []
    for model in models:
        model_path = os.path.join(base_dir, model)
        if not os.path.exists(model_path):
            missing_models.append(model)
        else:
            logger.info(f"✓ Modelo encontrado: {model}")
    
    return missing_models

def main():
    logger.info("=== Teste de Importações e Dependências ===")
    
    # Teste de importações
    logger.info("\n1. Testando importações...")
    import_errors = test_imports()
    
    # Teste de modelos
    logger.info("\n2. Testando modelos...")
    missing_models = test_model_loading()
    
    # Resumo
    logger.info("\n=== Resumo ===")
    
    if import_errors:
        logger.error("❌ Erros de importação:")
        for error in import_errors:
            logger.error(f"  - {error}")
    else:
        logger.info("✅ Todas as importações estão funcionando")
    
    if missing_models:
        logger.warning("⚠️  Modelos não encontrados:")
        for model in missing_models:
            logger.warning(f"  - {model}")
    else:
        logger.info("✅ Todos os modelos estão disponíveis")
    
    # Status final
    if not import_errors and not missing_models:
        logger.info("🎉 Sistema está pronto para executar!")
        return 0
    elif not import_errors:
        logger.info("✅ Sistema básico está funcionando (mas alguns modelos estão faltando)")
        return 0
    else:
        logger.error("❌ Sistema tem problemas que precisam ser resolvidos")
        return 1

if __name__ == "__main__":
    sys.exit(main())
