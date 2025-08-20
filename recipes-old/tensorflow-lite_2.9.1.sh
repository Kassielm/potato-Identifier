#!/bin/bash
source global_variables.sh
PN='tensorflow-lite'
PV='2.9.1'
S=${WORKDIR}'/tensorflow-imx'
SRCBRANCH='lf-5.15.71_2.2.0'
BUILD_NUM_JOBS=16
B='/tflite-build'

echo "🔧 Compilando TensorFlow Lite $PV para NPU iMX8MP..."

## Get Tensorflow Code ##
echo "📥 Baixando código fonte do TensorFlow IMX..."
git clone -b $SRCBRANCH https://github.com/nxp-imx/tensorflow-imx.git ${S}

## Compile TensorFlow Lite ##
echo "🔨 Compilando TensorFlow Lite..."
mkdir ${B}
cd ${B}

cmake \
    -DFETCHCONTENT_FULLY_DISCONNECTED=OFF \
    -DTFLITE_BUILD_SHARED_LIB=on \
    -DTFLITE_ENABLE_NNAPI=off \
    -DTFLITE_ENABLE_NNAPI_VERBOSE_VALIDATION=on \
    -DTFLITE_ENABLE_RUY=on \
    -DTFLITE_ENABLE_XNNPACK=on \
    -DTFLITE_PYTHON_WRAPPER_BUILD_CMAKE2=on \
    -DTFLITE_ENABLE_EXTERNAL_DELEGATE=on \
    ${S}/tensorflow/lite

cmake --build . -j ${BUILD_NUM_JOBS}

## Install libraries ##
echo "📦 Instalando bibliotecas..."
install -d ${D}${libdir}
cp --no-preserve=ownership -d ${B}/libtensorflow-lite.so.2.9.1 ${D}${libdir}/libtensorflow-lite.so

## Install header files ##
echo "📂 Instalando headers..."
install -d ${D}${includedir}/tensorflow/lite
cd ${S}/tensorflow/lite
cp --parents \
    $(find . -name "*.h*") \
    ${D}${includedir}/tensorflow/lite

# Install version.h from core
install -d ${D}${includedir}/tensorflow/core/public
cp ${S}/tensorflow/core/public/version.h ${D}${includedir}/tensorflow/core/public

## Install pkg-config file ##
echo "⚙️  Instalando pkg-config..."
install -d ${D}${libdir}/pkgconfig
install -m 0644 ${WORKDIR}/tensorflow-lite.pc.in ${D}${libdir}/pkgconfig/tensorflow2-lite.pc

sed -i 's:@version@:${PV}:g
    s:@libdir@:${libdir}:g
    s:@includedir@:${includedir}:g' ${D}${libdir}/pkgconfig/tensorflow2-lite.pc

## Build Python wheel ##
echo "🐍 Compilando wheel Python..."
cd ${B}
BUILD_NUM_JOBS=${BUILD_NUM_JOBS} ${S}/tensorflow/lite/tools/pip_package/build_pip_package_with_cmake2.sh
cp ${B}/tflite_pip/dist/tflite_runtime-2.9.1-cp311-cp311-linux_aarch64.whl ${D}/tflite_runtime-2.9.1-cp311-cp311-linux_aarch64.whl

echo "✅ TensorFlow Lite $PV compilado com sucesso!"
