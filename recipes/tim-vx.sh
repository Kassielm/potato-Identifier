#!/bin/bash
set -e
source build_variables.sh `basename "$0"`
source global_variables.sh
SRCBRANCH='lf-5.15.71_2.2.0'
TIM_VX_SRC='https://github.com/nxp-imx/tim-vx-imx.git'

echo "🔧 Compilando TIM-VX $SRCBRANCH para integração com NPU..."

EXTRA_OECMAKE=" \
  -DCONFIG=YOCTO \
  -DTIM_VX_ENABLE_TEST=off \
  -DTIM_VX_USE_EXTERNAL_OVXLIB=on \
  -DCMAKE_INSTALL_PREFIX=${D}/usr/ \
  -DCMAKE_INSTALL_LIBDIR=lib/ \
  -DOVXLIB_INC=/usr/include/${GCC_ARCH}/OVXLIB/ \
  -DOVXLIB_LIB=/usr/lib/${GCC_ARCH}/libovxlib.so
"

# Clone TIM-VX repository
echo "📥 Baixando código fonte do TIM-VX..."
pushd ${WORKDIR} && \
  git clone -b ${SRCBRANCH} ${TIM_VX_SRC} ${S} && \
  popd

# Build TIM-VX
echo "🔨 Compilando TIM-VX..."
pushd ${S} && \
  git clean -df && \
  # Remove -Werror flags that may cause compilation issues
  find . -name "BUILD" -exec sed -i 's/-Werror,\? //g' {} \; 2>/dev/null || true && \
  find . -name "BUILD" -exec sed -i 's/, *-Werror//g' {} \; 2>/dev/null || true && \
  find . -name "CMakeLists.txt" -exec sed -i 's/-Werror//g' {} \; 2>/dev/null || true && \
  find . -name "makefile.linux" -exec sed -i 's/-Werror//g' {} \; 2>/dev/null || true && \
  mkdir build && pushd build && \
  cmake ${EXTRA_OECMAKE} .. && make -j`nproc` all install && \
  popd && popd

# Copy installed libraries to rootfs
echo "📦 Instalando TIM-VX..."
cp -r ${D}/* /
ldconfig

echo "✅ TIM-VX compilado e instalado com sucesso!"
