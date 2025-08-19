#!/bin/bash
source global_variables.sh
PN='tensorflow-lite'
PV='2.9.1'
T=${WORKDIR}'/tensorflow-imx'
S=${WORKDIR}'/tflite-vx-delegate-imx'
SRCBRANCH='lf-5.15.71_2.2.0'
BUILD_NUM_JOBS=16
VX_IMX_SRC='https://github.com/nxp-imx/tflite-vx-delegate-imx.git'
B='/tflite-vx-delegate-imx-build'

echo "🔧 Compilando VX Delegate para NPU iMX8MP..."

# Clone VX delegate repository
echo "📥 Baixando código fonte do VX Delegate..."
pushd ${WORKDIR} && git clone -b ${SRCBRANCH} ${VX_IMX_SRC} ${S} && popd

# Build VX delegate
echo "🔨 Compilando VX Delegate..."

# Check if TensorFlow Lite library exists
if [ ! -f "${D}${libdir}/libtensorflow-lite.so" ]; then
    echo "❌ ERRO: TensorFlow Lite library não encontrada em ${D}${libdir}/libtensorflow-lite.so"
    echo "Verifique se tensorflow-lite_2.9.1.sh foi executado antes!"
    ls -la ${D}${libdir}/ || echo "Diretório ${D}${libdir}/ não existe"
    exit 1
fi

echo "✅ TensorFlow Lite library encontrada: ${D}${libdir}/libtensorflow-lite.so"

mkdir ${B}
cd ${B}
cmake ${S} \
        -DFETCHCONTENT_FULLY_DISCONNECTED=OFF \
        -DTIM_VX_INSTALL=${D}/usr \
        -DFETCHCONTENT_SOURCE_DIR_TENSORFLOW=${T} \
        -DTFLITE_LIB_LOC=${D}${libdir}/libtensorflow-lite.so 

make vx_delegate -j ${BUILD_NUM_JOBS}

# Install VX delegate library
echo "📦 Instalando VX Delegate..."
install -d ${D}${libdir}

# Check if the built library exists
if [ -f "${B}/libvx_delegate.so" ]; then
    echo "✅ VX delegate compiled successfully: ${B}/libvx_delegate.so"
    cp --no-preserve=ownership -d ${B}/libvx_delegate.so ${D}${libdir}
    echo "✅ VX delegate installed to: ${D}${libdir}/libvx_delegate.so"
    
    # Verify the installation
    ls -la ${D}${libdir}/libvx_delegate.so
else
    echo "❌ ERRO: VX delegate compilation failed! libvx_delegate.so not found in ${B}/"
    echo "Conteúdo do diretório de build:"
    ls -la ${B}/ || echo "Diretório de build não existe"
    exit 1
fi

# Install header files (optional, for development)
install -d ${D}${includedir}/tensorflow-lite-vx-delegate
cd ${S}
cp --parents \
    $(find . -name "*.h*") \
    ${D}${includedir}/tensorflow-lite-vx-delegate

echo "✅ VX Delegate compilado e instalado com sucesso!"


