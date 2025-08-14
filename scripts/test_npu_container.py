#!/usr/bin/env python3
"""
Script de teste para verificar NPU dentro do container
"""

import os
import sys
import subprocess
import time

def test_npu_detection():
    """Testa detecção do NPU"""
    print("🔍 Verificando detecção do NPU...")
    
    # Verificar dispositivos VIP
    vip_devices = ['/dev/vipnpu', '/dev/galcore']
    found_devices = []
    
    for device in vip_devices:
        if os.path.exists(device):
            found_devices.append(device)
            print(f"✅ Dispositivo encontrado: {device}")
        else:
            print(f"❌ Dispositivo não encontrado: {device}")
    
    return len(found_devices) > 0

def test_delegate_loading():
    """Testa carregamento de delegates"""
    print("\n🔧 Testando carregamento de delegates...")
    
    try:
        import tflite_runtime.interpreter as tflite
        
        # Testar delegate VX
        delegate_paths = [
            '/usr/lib/libvx_delegate.so',
            '/usr/lib/aarch64-linux-gnu/libvx_delegate.so',
            '/opt/venv/lib/python3.*/site-packages/tflite_runtime/libvx_delegate.so'
        ]
        
        for path in delegate_paths:
            if '*' in path:
                # Expandir wildcard
                import glob
                matches = glob.glob(path)
                if matches:
                    path = matches[0]
                else:
                    continue
            
            if os.path.exists(path):
                try:
                    delegate = tflite.load_delegate(path)
                    print(f"✅ Delegate carregado: {path}")
                    return True
                except Exception as e:
                    print(f"❌ Erro ao carregar delegate {path}: {e}")
            else:
                print(f"⚠️ Delegate não encontrado: {path}")
        
        return False
        
    except ImportError as e:
        print(f"❌ Erro ao importar TensorFlow Lite: {e}")
        return False

def test_model_inference():
    """Testa inferência com modelo"""
    print("\n🎯 Testando inferência com modelo...")
    
    try:
        import tflite_runtime.interpreter as tflite
        import numpy as np
        
        # Verificar se existe modelo quantizado
        model_paths = [
            '/app/data/models/best_float32_edgetpu.tflite',
            '/app/data/models/best_float32.tflite'
        ]
        
        model_path = None
        for path in model_paths:
            if os.path.exists(path):
                model_path = path
                break
        
        if not model_path:
            print("❌ Nenhum modelo encontrado")
            return False
        
        print(f"📄 Usando modelo: {model_path}")
        
        # Tentar carregar com delegate VX
        try:
            delegate = tflite.load_delegate('/usr/lib/libvx_delegate.so')
            interpreter = tflite.Interpreter(
                model_path=model_path,
                experimental_delegates=[delegate]
            )
            print("✅ Modelo carregado com delegate VX")
        except:
            # Fallback para CPU
            interpreter = tflite.Interpreter(model_path=model_path)
            print("⚠️ Modelo carregado em CPU (fallback)")
        
        interpreter.allocate_tensors()
        
        # Obter informações do modelo
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()
        
        print(f"📊 Input shape: {input_details[0]['shape']}")
        print(f"📊 Output shape: {output_details[0]['shape']}")
        
        # Teste com dados dummy
        input_shape = input_details[0]['shape']
        dummy_input = np.random.randint(0, 255, size=input_shape, dtype=np.uint8)
        
        start_time = time.time()
        interpreter.set_tensor(input_details[0]['index'], dummy_input)
        interpreter.invoke()
        inference_time = time.time() - start_time
        
        print(f"⚡ Tempo de inferência: {inference_time:.3f}s")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante teste de inferência: {e}")
        return False

def main():
    """Função principal"""
    print("🧪 Teste de NPU no Container")
    print("=" * 40)
    
    results = []
    
    # Teste 1: Detecção do NPU
    results.append(test_npu_detection())
    
    # Teste 2: Carregamento de delegates
    results.append(test_delegate_loading())
    
    # Teste 3: Inferência com modelo
    results.append(test_model_inference())
    
    # Resultado final
    print("\n📋 Resumo dos Testes:")
    print("=" * 30)
    
    tests = [
        "Detecção do NPU",
        "Carregamento de Delegates",
        "Inferência com Modelo"
    ]
    
    for i, (test, result) in enumerate(zip(tests, results)):
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{i+1}. {test}: {status}")
    
    success_rate = sum(results) / len(results) * 100
    print(f"\n🎯 Taxa de Sucesso: {success_rate:.1f}%")
    
    if success_rate >= 66.7:
        print("🎉 NPU está funcionando adequadamente!")
        return 0
    else:
        print("⚠️ Alguns problemas detectados com o NPU")
        return 1

if __name__ == "__main__":
    sys.exit(main())
