#!/usr/bin/env python3
"""
Script para verificar disponibilidade da NPU e delegates no Verdin iMX8MP
"""

import os
import sys
import logging
import subprocess

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def check_device_tree():
    """Verifica se estamos em um Verdin iMX8MP através do device tree."""
    try:
        with open('/proc/device-tree/compatible', 'r') as f:
            compatible = f.read()
            if 'verdin-imx8mp' in compatible:
                logger.info("✅ Verdin iMX8MP detectado via device tree")
                return True
            else:
                logger.warning(f"⚠️  Device tree compatível: {compatible.strip()}")
                return False
    except Exception as e:
        logger.warning(f"⚠️  Não foi possível ler device tree: {e}")
        return False

def check_hardware_devices():
    """Verifica dispositivos de hardware disponíveis."""
    logger.info("🔍 Verificando dispositivos de hardware...")
    
    devices_to_check = [
        ('/dev/galcore', 'Galcore GPU'),
        ('/dev/dri/card0', 'DRI GPU Card 0'),
        ('/dev/dri/renderD128', 'DRI Render Node'),
        ('/dev/vipnpu', 'VIP NPU'),
        ('/dev/mxc_hantro', 'Hantro VPU'),
        ('/dev/mxc_hantro_vc8000e', 'Hantro VC8000E Encoder'),
    ]
    
    available_devices = []
    for device_path, device_name in devices_to_check:
        if os.path.exists(device_path):
            try:
                stat = os.stat(device_path)
                logger.info(f"✅ {device_name}: {device_path} (modo: {oct(stat.st_mode)[-3:]})")
                available_devices.append(device_name)
            except Exception as e:
                logger.warning(f"⚠️  {device_name}: {device_path} existe mas erro ao acessar: {e}")
        else:
            logger.info(f"❌ {device_name}: {device_path} não encontrado")
    
    return available_devices

def check_tflite_runtime():
    """Verifica se o TensorFlow Lite Runtime está disponível."""
    try:
        import tflite_runtime.interpreter as tflite
        logger.info("✅ TensorFlow Lite Runtime disponível")
        logger.info(f"   Versão: {tflite.__version__ if hasattr(tflite, '__version__') else 'Desconhecida'}")
        return True
    except ImportError as e:
        logger.error(f"❌ TensorFlow Lite Runtime não disponível: {e}")
        return False

def check_delegates():
    """Verifica se os delegates estão disponíveis."""
    logger.info("🧠 Verificando delegates...")
    
    delegate_paths = [
        '/usr/lib/libvx_delegate.so',
        '/usr/lib/aarch64-linux-gnu/libvx_delegate.so',
        '/usr/local/lib/libvx_delegate.so',
    ]
    
    available_delegates = []
    for delegate_path in delegate_paths:
        if os.path.exists(delegate_path):
            try:
                stat = os.stat(delegate_path)
                size = stat.st_size
                logger.info(f"✅ Delegate VX encontrado: {delegate_path} ({size} bytes)")
                available_delegates.append(delegate_path)
                
                # Verificar se é carregável
                try:
                    result = subprocess.run(['ldd', delegate_path], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        logger.info(f"   ✅ Delegate é carregável")
                    else:
                        logger.warning(f"   ⚠️  Delegate pode ter dependências não satisfeitas")
                except Exception as e:
                    logger.warning(f"   ⚠️  Erro ao verificar dependências: {e}")
                
            except Exception as e:
                logger.warning(f"⚠️  Delegate encontrado mas erro ao acessar: {e}")
        else:
            logger.info(f"❌ Delegate não encontrado: {delegate_path}")
    
    return available_delegates

def test_delegate_loading():
    """Testa carregamento do delegate."""
    logger.info("🧪 Testando carregamento do delegate...")
    
    try:
        import tflite_runtime.interpreter as tflite
        
        delegate_paths = [
            '/usr/lib/libvx_delegate.so',
            '/usr/lib/aarch64-linux-gnu/libvx_delegate.so',
        ]
        
        for delegate_path in delegate_paths:
            if os.path.exists(delegate_path):
                try:
                    logger.info(f"   Tentando carregar: {delegate_path}")
                    delegate = tflite.load_delegate(delegate_path)
                    logger.info(f"✅ Delegate carregado com sucesso: {delegate_path}")
                    return True
                except Exception as e:
                    logger.warning(f"⚠️  Erro ao carregar delegate {delegate_path}: {e}")
        
        logger.error("❌ Nenhum delegate pôde ser carregado")
        return False
        
    except ImportError:
        logger.error("❌ TensorFlow Lite Runtime não disponível para teste")
        return False

def check_npu_environment():
    """Verifica variáveis de ambiente relacionadas à NPU."""
    logger.info("🌍 Verificando variáveis de ambiente...")
    
    env_vars = [
        'NPU_AVAILABLE',
        'VIV_MGPU_KERNEL_CONFIG',
        'CORAL_ENABLE_EDGETPU',
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            logger.info(f"✅ {var}={value}")
        else:
            logger.info(f"❌ {var} não definida")

def generate_test_script():
    """Gera um script de teste para usar a NPU."""
    test_script = '''#!/usr/bin/env python3
"""
Script de teste para NPU no Verdin iMX8MP
"""

import os
import numpy as np
import tflite_runtime.interpreter as tflite

def test_npu():
    print("🧠 Testando NPU...")
    
    # Tentar carregar delegate
    delegate_path = "/usr/lib/libvx_delegate.so"
    if not os.path.exists(delegate_path):
        print(f"❌ Delegate não encontrado: {delegate_path}")
        return False
    
    try:
        print(f"   Carregando delegate: {delegate_path}")
        delegate = tflite.load_delegate(delegate_path)
        print("✅ Delegate carregado com sucesso")
        
        # Criar um interpretador simples para teste
        # (você precisará de um modelo .tflite para teste real)
        print("💡 Para teste completo, use um modelo .tflite real")
        print("   Exemplo: interpreter = tflite.Interpreter(model_path='modelo.tflite', experimental_delegates=[delegate])")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao carregar delegate: {e}")
        return False

if __name__ == "__main__":
    test_npu()
'''
    
    script_path = '/tmp/test_npu.py'
    with open(script_path, 'w') as f:
        f.write(test_script)
    
    os.chmod(script_path, 0o755)
    logger.info(f"📝 Script de teste gerado: {script_path}")
    return script_path

def main():
    """Função principal de verificação."""
    print("🔍 Verificação da NPU no Verdin iMX8MP")
    print("=" * 50)
    
    # Verificações
    is_verdin = check_device_tree()
    available_devices = check_hardware_devices()
    tflite_ok = check_tflite_runtime()
    available_delegates = check_delegates()
    check_npu_environment()
    
    print("\n" + "=" * 50)
    print("📊 RESUMO:")
    
    if is_verdin:
        print("✅ Hardware: Verdin iMX8MP detectado")
    else:
        print("⚠️  Hardware: Não confirmado como Verdin iMX8MP")
    
    if available_devices:
        print(f"✅ Dispositivos: {len(available_devices)} encontrado(s)")
        for device in available_devices:
            print(f"   - {device}")
    else:
        print("❌ Dispositivos: Nenhum dispositivo de aceleração encontrado")
    
    if tflite_ok:
        print("✅ TensorFlow Lite: Disponível")
    else:
        print("❌ TensorFlow Lite: Não disponível")
    
    if available_delegates:
        print(f"✅ Delegates: {len(available_delegates)} encontrado(s)")
        delegate_test_ok = test_delegate_loading()
        if delegate_test_ok:
            print("✅ Teste de Delegate: Carregamento bem-sucedido")
        else:
            print("❌ Teste de Delegate: Falha no carregamento")
    else:
        print("❌ Delegates: Nenhum delegate encontrado")
    
    # Gerar script de teste
    test_script = generate_test_script()
    
    print("\n💡 PRÓXIMOS PASSOS:")
    if not available_delegates:
        print("1. Execute: sudo /app/scripts/install_delegates.sh")
        print("2. Execute novamente este script para verificar")
    else:
        print(f"1. Execute o script de teste: python3 {test_script}")
        print("2. Use um modelo .tflite quantizado (INT8) para melhor performance na NPU")
    
    print("\n🔗 LINKS ÚTEIS:")
    print("- Documentação Toradex: https://developer.toradex.com/")
    print("- TensorFlow Lite: https://www.tensorflow.org/lite")

if __name__ == "__main__":
    main()
