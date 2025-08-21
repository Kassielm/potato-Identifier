#!/usr/bin/env python3
"""
Script para diagnosticar problemas com NPU e delegates
"""

import os
import subprocess
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_system_info():
    """Verificar informações do sistema"""
    logger.info("🔍 VERIFICANDO SISTEMA")
    logger.info("=" * 50)
    
    # Verificar arquitetura
    try:
        arch = subprocess.check_output(['uname', '-m']).decode().strip()
        logger.info(f"Arquitetura: {arch}")
    except:
        logger.warning("Não foi possível obter arquitetura")
    
    # Verificar dispositivos
    devices_to_check = [
        '/dev/vipnpu',
        '/dev/video0',
        '/dev/video1', 
        '/dev/video2'
    ]
    
    for device in devices_to_check:
        if os.path.exists(device):
            logger.info(f"✅ Dispositivo encontrado: {device}")
        else:
            logger.warning(f"⚠️ Dispositivo não encontrado: {device}")

def check_libraries():
    """Verificar bibliotecas disponíveis"""
    logger.info("\n🔍 VERIFICANDO BIBLIOTECAS")
    logger.info("=" * 50)
    
    libraries_to_check = [
        '/usr/lib/libvx_delegate.so',
        '/usr/lib/libnnapi_delegate.so',
        '/usr/lib/aarch64-linux-gnu/libvx_delegate.so',
        '/usr/lib/arm-linux-gnueabihf/libvx_delegate.so'
    ]
    
    for lib in libraries_to_check:
        if os.path.exists(lib):
            logger.info(f"✅ Biblioteca encontrada: {lib}")
        else:
            logger.warning(f"⚠️ Biblioteca não encontrada: {lib}")

def check_environment():
    """Verificar variáveis de ambiente"""
    logger.info("\n🔍 VERIFICANDO VARIÁVEIS DE AMBIENTE")
    logger.info("=" * 50)
    
    env_vars = [
        'NPU_AVAILABLE',
        'VIPNPU_DEVICE',
        'VIV_MGPU_KERNEL_CONFIG',
        'IMX_VPU_ENABLE_TILE_OPTIMIZE',
        'TF_CPP_MIN_LOG_LEVEL',
        'CORAL_ENABLE_EDGETPU',
        'OMP_NUM_THREADS',
        'TF_NUM_INTEROP_THREADS',
        'TF_NUM_INTRAOP_THREADS'
    ]
    
    for var in env_vars:
        value = os.getenv(var, 'Não definida')
        logger.info(f"{var}: {value}")

def check_tensorflow():
    """Verificar instalação do TensorFlow"""
    logger.info("\n🔍 VERIFICANDO TENSORFLOW")
    logger.info("=" * 50)
    
    try:
        import tflite_runtime.interpreter as tflite
        from tflite_runtime.interpreter import load_delegate
        logger.info("✅ tflite_runtime disponível")
        
        # Verificar versão se possível
        try:
            version = tflite.__version__
            logger.info(f"Versão: {version}")
        except:
            logger.info("Versão não disponível")
            
    except ImportError:
        logger.warning("⚠️ tflite_runtime não disponível")
        
        try:
            import tensorflow as tf
            logger.info("✅ tensorflow completo disponível")
            logger.info(f"Versão: {tf.__version__}")
        except ImportError:
            logger.error("❌ Nenhuma versão do TensorFlow encontrada")

def check_npu_device():
    """Verificar dispositivo NPU especificamente"""
    logger.info("\n🔍 VERIFICANDO DISPOSITIVO NPU")
    logger.info("=" * 50)
    
    npu_device = "/dev/vipnpu"
    
    if os.path.exists(npu_device):
        logger.info(f"✅ Dispositivo NPU encontrado: {npu_device}")
        
        try:
            # Verificar permissões
            stat_info = os.stat(npu_device)
            logger.info(f"Permissões: {oct(stat_info.st_mode)[-3:]}")
            logger.info(f"Proprietário: {stat_info.st_uid}:{stat_info.st_gid}")
            
            # Verificar se é acessível
            if os.access(npu_device, os.R_OK):
                logger.info("✅ Dispositivo legível")
            else:
                logger.warning("⚠️ Dispositivo não legível")
                
            if os.access(npu_device, os.W_OK):
                logger.info("✅ Dispositivo gravável")
            else:
                logger.warning("⚠️ Dispositivo não gravável")
                
        except Exception as e:
            logger.error(f"❌ Erro ao verificar permissões: {e}")
    else:
        logger.error(f"❌ Dispositivo NPU não encontrado: {npu_device}")

def test_simple_delegate():
    """Teste simples de carregamento do delegate"""
    logger.info("\n🔍 TESTANDO CARREGAMENTO DO DELEGATE")
    logger.info("=" * 50)
    
    try:
        from tflite_runtime.interpreter import load_delegate
        
        vx_delegate_path = "/usr/lib/libvx_delegate.so"
        
        if os.path.exists(vx_delegate_path):
            try:
                delegate = load_delegate(vx_delegate_path)
                logger.info("✅ VX Delegate carregado com sucesso")
                
                # Tentar criar um interpretador simples
                import tflite_runtime.interpreter as tflite
                
                # Criar um modelo mínimo de teste (se não houver modelo disponível)
                # Apenas teste de carregamento do delegate
                logger.info("✅ Delegate pronto para uso")
                
            except Exception as e:
                logger.error(f"❌ Erro ao carregar VX Delegate: {e}")
        else:
            logger.error(f"❌ VX Delegate não encontrado: {vx_delegate_path}")
            
    except ImportError as e:
        logger.error(f"❌ Erro ao importar load_delegate: {e}")

def main():
    """Função principal do diagnóstico"""
    logger.info("🚀 INICIANDO DIAGNÓSTICO NPU")
    logger.info("=" * 50)
    
    check_system_info()
    check_libraries()
    check_environment()
    check_tensorflow()
    check_npu_device()
    test_simple_delegate()
    
    logger.info("\n🏁 DIAGNÓSTICO CONCLUÍDO")
    logger.info("=" * 50)
    
    logger.info("\n💡 PRÓXIMOS PASSOS:")
    logger.info("1. Execute o script test_models.py para testar modelos específicos")
    logger.info("2. Se o NPU não estiver funcionando, tente executar sem delegates")
    logger.info("3. Verifique se o container tem privilégios adequados")
    logger.info("4. Considere usar um modelo diferente se houver incompatibilidade")

if __name__ == "__main__":
    main()
