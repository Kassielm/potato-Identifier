#!/bin/bash
source global_variables.sh
PN='nn-imx'
PV='1.3.0'
S=${WORKDIR}'/'${PN}
SRCBRANCH='imx_1.3.0'
NN_IMX_SRC='https://github.com/nxp-imx/nn-imx.git'

echo "🔧 Compilando NN-IMX $PV para suporte NPU..."

# Clone and build NN-IMX
echo "📥 Baixando código fonte do NN-IMX..."
pushd ${WORKDIR} && git clone -b ${SRCBRANCH} ${NN_IMX_SRC} ${S} && popd

echo "🔨 Compilando NN-IMX..."
pushd ${S} && AQROOT=${S} make -j`nproc` && popd

# Install libraries and headers
echo "📦 Instalando bibliotecas e headers..."
install -d ${libdir}/${GCC_ARCH}
install -d ${includedir}/${GCC_ARCH}/OVXLIB
install -d ${includedir}/${GCC_ARCH}/nnrt
cp -d ${S}/*.so* ${libdir}/${GCC_ARCH}
cp -r ${S}/include/OVXLIB/* ${includedir}/${GCC_ARCH}/OVXLIB/
cp -r ${S}/include/nnrt/* ${includedir}/${GCC_ARCH}/nnrt/

echo "✅ NN-IMX $PV compilado e instalado com sucesso!"
