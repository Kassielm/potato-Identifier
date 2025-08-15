#!/usr/bin/env python3
"""
Script para verificar informações dos modelos TFLite
"""

import os
import sys

def check_model_info():
    """Verifica informações dos modelos disponíveis"""
    
    # Importar TensorFlow Lite
    try:
        import tflite_runtime.interpreter as tflite
        print("✅ TensorFlow Lite Runtime disponível")
    except ImportError:
        try:
            import tensorflow as tf
            tflite = tf.lite
            print("✅ TensorFlow Lite (do TensorFlow completo) disponível")
        except ImportError:
            print("❌ TensorFlow Lite não disponível")
            return False
    
    models_dir = "/app/data/models"
    models = [
        "best_int8.tflite",
        "best_float32_edgetpu.tflite", 
        "best_float32.tflite"
    ]
    
    print(f"\n📁 Verificando modelos em: {models_dir}")
    
    for model_name in models:
        model_path = os.path.join(models_dir, model_name)
        print(f"\n🔍 Analisando: {model_name}")
        
        if not os.path.exists(model_path):
            print(f"   ❌ Arquivo não encontrado: {model_path}")
            continue
            
        try:
            # Carregar modelo
            interpreter = tflite.Interpreter(model_path=model_path)
            interpreter.allocate_tensors()
            
            # Obter detalhes de entrada
            input_details = interpreter.get_input_details()
            output_details = interpreter.get_output_details()
            
            print(f"   ✅ Modelo carregado com sucesso")
            print(f"   📊 Input shape: {input_details[0]['shape']}")
            print(f"   🔢 Input dtype: {input_details[0]['dtype']}")
            print(f"   📤 Outputs: {len(output_details)}")
            
            # Verificar se é quantizado
            if input_details[0]['dtype'] == 'uint8':
                print(f"   🎯 MODELO QUANTIZADO (INT8) - Ideal para NPU!")
            else:
                print(f"   💻 Modelo float - CPU/GPU")
                
            # Obter tamanho do arquivo
            file_size = os.path.getsize(model_path) / (1024 * 1024)  # MB
            print(f"   💾 Tamanho: {file_size:.2f} MB")
            
        except Exception as e:
            print(f"   ❌ Erro ao carregar modelo: {e}")
    
    return True

if __name__ == "__main__":
    if check_model_info():
        print("\n✅ Verificação concluída!")
    else:
        print("\n❌ Verificação falhou!")
        sys.exit(1)
