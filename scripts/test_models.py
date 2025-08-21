#!/usr/bin/env python3
"""
Script para verificar e testar modelos TensorFlow Lite
Útil para diagnosticar problemas de compatibilidade com delegates
"""

import os
import logging
import sys

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Tenta importar tflite_runtime primeiro
try:
    import tflite_runtime.interpreter as tflite
    from tflite_runtime.interpreter import load_delegate
    USING_TFLITE_RUNTIME = True
    DELEGATES_AVAILABLE = True
    logger.info("✅ Usando tflite_runtime")
except ImportError:
    try:
        import tensorflow as tf_full
        tflite = tf_full.lite
        from tensorflow.lite.python.interpreter import load_delegate
        USING_TFLITE_RUNTIME = False
        DELEGATES_AVAILABLE = True
        logger.info("✅ Usando tensorflow completo")
    except ImportError:
        logger.error("❌ Não foi possível importar TensorFlow Lite")
        sys.exit(1)

def test_model(model_path, use_delegate=False):
    """Testa um modelo específico"""
    logger.info(f"\n{'='*60}")
    logger.info(f"🧪 Testando modelo: {os.path.basename(model_path)}")
    logger.info(f"   Caminho: {model_path}")
    logger.info(f"   Usar delegate: {use_delegate}")
    
    if not os.path.exists(model_path):
        logger.error(f"❌ Modelo não encontrado: {model_path}")
        return False
    
    # Obter informações do arquivo
    file_size = os.path.getsize(model_path) / (1024 * 1024)  # MB
    logger.info(f"   Tamanho: {file_size:.2f} MB")
    
    try:
        delegates = []
        
        if use_delegate and DELEGATES_AVAILABLE:
            try:
                vx_delegate_path = "/usr/lib/libvx_delegate.so"
                if os.path.exists(vx_delegate_path):
                    vx_delegate = load_delegate(vx_delegate_path)
                    delegates.append(vx_delegate)
                    logger.info("   ✅ VX Delegate carregado")
                else:
                    logger.warning("   ⚠️ VX Delegate não encontrado")
                    
            except Exception as e:
                logger.warning(f"   ⚠️ Erro ao carregar delegate: {e}")
        
        # Carregar modelo
        if delegates:
            interpreter = tflite.Interpreter(
                model_path=model_path,
                experimental_delegates=delegates
            )
            logger.info(f"   📊 Modelo carregado com {len(delegates)} delegate(s)")
        else:
            interpreter = tflite.Interpreter(model_path=model_path)
            logger.info("   📊 Modelo carregado em CPU")
        
        # Alocar tensors
        interpreter.allocate_tensors()
        logger.info("   ✅ Tensors alocados com sucesso")
        
        # Obter detalhes
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()
        
        logger.info(f"   📥 Entradas: {len(input_details)}")
        for i, detail in enumerate(input_details):
            logger.info(f"      {i}: shape={detail['shape']}, dtype={detail['dtype']}")
            
        logger.info(f"   📤 Saídas: {len(output_details)}")
        for i, detail in enumerate(output_details):
            logger.info(f"      {i}: shape={detail['shape']}, dtype={detail['dtype']}")
        
        logger.info("   ✅ Teste concluído com sucesso!")
        return True
        
    except Exception as e:
        logger.error(f"   ❌ Erro no teste: {e}")
        return False

def main():
    """Função principal"""
    logger.info("🚀 Iniciando verificação de modelos TensorFlow Lite")
    
    # Caminhos dos modelos
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    models_dir = os.path.join(base_dir, 'data', 'models')
    
    models = [
        'lite-model_ssd_mobilenet_v1_1_metadata_2.tflite',
        'best_float32.tflite',
        'best_full_integer_quant.tflite',
        'best_int8_potato.tflite',
        'best_integer_quant.tflite'
    ]
    
    logger.info(f"📁 Diretório de modelos: {models_dir}")
    
    # Verificar NPU
    npu_available = os.getenv('NPU_AVAILABLE', '0') == '1'
    vx_delegate_exists = os.path.exists("/usr/lib/libvx_delegate.so")
    
    logger.info(f"🧠 Status do NPU:")
    logger.info(f"   NPU_AVAILABLE: {npu_available}")
    logger.info(f"   VX Delegate: {vx_delegate_exists}")
    logger.info(f"   Delegates disponíveis: {DELEGATES_AVAILABLE}")
    
    results = {}
    
    # Testar cada modelo
    for model_name in models:
        model_path = os.path.join(models_dir, model_name)
        
        if not os.path.exists(model_path):
            logger.warning(f"⚠️ Modelo não encontrado: {model_name}")
            continue
        
        # Teste 1: CPU apenas
        cpu_result = test_model(model_path, use_delegate=False)
        
        # Teste 2: Com delegate (se disponível)
        delegate_result = False
        if npu_available and vx_delegate_exists and DELEGATES_AVAILABLE:
            delegate_result = test_model(model_path, use_delegate=True)
        
        results[model_name] = {
            'cpu': cpu_result,
            'delegate': delegate_result
        }
    
    # Resumo dos resultados
    logger.info(f"\n{'='*60}")
    logger.info("📊 RESUMO DOS RESULTADOS")
    logger.info(f"{'='*60}")
    
    for model_name, result in results.items():
        logger.info(f"📄 {model_name}:")
        logger.info(f"   CPU: {'✅' if result['cpu'] else '❌'}")
        logger.info(f"   NPU: {'✅' if result['delegate'] else '❌' if npu_available else 'N/A'}")
    
    # Recomendações
    logger.info(f"\n{'='*60}")
    logger.info("💡 RECOMENDAÇÕES")
    logger.info(f"{'='*60}")
    
    # Encontrar melhor modelo para CPU
    cpu_models = [name for name, result in results.items() if result['cpu']]
    if cpu_models:
        logger.info(f"✅ Modelos funcionando em CPU: {', '.join(cpu_models)}")
    
    # Encontrar melhor modelo para NPU
    npu_models = [name for name, result in results.items() if result['delegate']]
    if npu_models:
        logger.info(f"✅ Modelos funcionando com NPU: {', '.join(npu_models)}")
        logger.info(f"💡 Recomendação: Use {npu_models[0]} para melhor performance")
    else:
        logger.warning("⚠️ Nenhum modelo funcionou com NPU - use CPU apenas")
        if cpu_models:
            logger.info(f"💡 Recomendação: Use {cpu_models[0]} em CPU")

if __name__ == "__main__":
    main()
