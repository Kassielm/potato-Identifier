#!/bin/bash
set -e
source build_variables.sh `basename "$0"`
source global_variables.sh
THIS_DIR=$(cd $(dirname $0) && pwd)
SRCBRANCH='lf-5.15.71_2.2.0'
TIM_VX_SRC='https://github.com/nxp-imx/tim-vx-imx.git'
PKG_CONFIG_SYSROOT_DIR="/"

EXTRA_OECMAKE=" \
  -DCONFIG=YOCTO \
  -DTIM_VX_ENABLE_TEST=off \
  -DTIM_VX_USE_EXTERNAL_OVXLIB=on \
  -DCMAKE_INSTALL_PREFIX=${D}/usr/ \
  -DCMAKE_INSTALL_LIBDIR=lib/ \
  -DOVXLIB_INC=/usr/include/${GCC_ARCH}/OVXLIB/ \
  -DOVXLIB_LIB=/usr/lib/${GCC_ARCH}/libovxlib.so
"

pushd ${WORKDIR} && \
  git clone -b ${SRCBRANCH} ${TIM_VX_SRC} ${S} && \
  popd

pushd ${S} && \
  git clean -df && \
  echo "Checking git status before applying patch..." && \
  git status && \
  echo "Attempting to apply patch..." && \
  if git apply --check ${D}/tim-vx-remove-Werror.patch 2>/dev/null; then \
    echo "Applying patch successfully..." && \
    git apply ${D}/tim-vx-remove-Werror.patch; \
  elif git apply --3way ${D}/tim-vx-remove-Werror.patch 2>/dev/null; then \
    echo "Applied patch with 3-way merge..."; \
  else \
    echo "Patch application failed, manually removing -Werror flags..." && \
    find . -name "BUILD" -exec sed -i 's/-Werror,\? //g' {} \; && \
    find . -name "BUILD" -exec sed -i 's/, *-Werror//g' {} \; && \
    find . -name "CMakeLists.txt" -exec sed -i 's/-Werror//g' {} \; && \
    find . -name "makefile.linux" -exec sed -i 's/-Werror//g' {} \; && \
    echo "Manually removed -Werror flags from build files"; \
  fi && \
  mkdir build && pushd build && \
  cmake ${EXTRA_OECMAKE} .. && make -j`nproc` all install && \
  popd && popd

# Copy installed libraries to rootfs #
cp -r ${D}/* /
# Reload libraries #
ldconfig
# Clean build directory #
rm -rf ${WORKDIR}
