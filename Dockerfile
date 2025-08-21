# Dockerfile para aplicação GUI na placa Toradex Verdin iMX8MP
# Baseado em imagem com suporte gráfico para TorizonCore

# --------------------
# Stage: tflite-build
# --------------------
FROM --platform=linux/arm64/v8 torizon/debian:3-bookworm AS tflite-build

## Install Python
RUN apt-get -y update && apt-get install -y \
  python3 python3-dev python3-numpy python3-pybind11 \
  python3-pip python3-setuptools python3-wheel \
  && apt-get clean && apt-get autoremove && rm -rf /var/lib/apt/lists/*

## Install build tools
RUN apt-get -y update && apt-get install -y \
    cmake build-essential gcc g++ git wget unzip patchelf \
    autoconf automake libtool curl gfortran

## Install dependencies
RUN apt-get -y update && apt-get install -y \
    zlib1g zlib1g-dev libssl-dev \
    imx-gpu-viv-wayland-dev openssl libffi-dev libjpeg-dev

WORKDIR /build
COPY recipes /build

### Install TensorFlow Lite
RUN chmod +x *.sh
RUN ./nn-imx_1.3.0.sh
RUN ./tim-vx.sh
RUN ./tensorflow-lite_2.9.1.sh
RUN ./tflite-vx-delegate.sh
# --------------------
# Stage: base (runtime GUI)
# --------------------

FROM --platform=linux/arm64/v8 torizon/debian:3-bookworm AS base

## Install build tools
RUN apt-get -y update && apt-get install -y \
    cmake build-essential gcc g++ git wget unzip patchelf \
    autoconf automake libtool curl gfortran

# Instalar pacotes do sistema
RUN apt-get -q -y update && \
    apt-get -q -y install --no-install-recommends \
        python3-minimal \
        python3-pip \
        python3-dev \
        python3-venv \
        libgl1 \
        libglib2.0-0 \
        libxext6 \
        libxrender1 \
        libxcb-xinerama0 \
        libxcb-cursor0 \
        python3-setuptools \
        python3-wheel \
        python3-tk \
        python3-pil \
        python3-pil.imagetk \
        build-essential \
        pkg-config \
        libhdf5-dev \
        libc-ares-dev \
        libeigen3-dev \
        libatlas-base-dev \
        libopenblas-dev \
        liblapack-dev \
        libcurl4-openssl-dev \
        libharfbuzz-dev \
        libfribidi-dev \
        libfreetype6-dev \
        libpng-dev \
        libtiff5-dev \
        libjpeg-dev \
        libopenjp2-7-dev \
        libwebp-dev \
        tcl8.6-dev \
        tk8.6-dev \
        python3-tk \
        ffmpeg \
        libsm6 \
        libxext6 \
        libxrender-dev \
        libgl1-mesa-glx \
        libglib2.0-0 \
        libgtk-3-0 \
        libgdk-pixbuf2.0-0 \
        libxss1 \
        libgconf-2-4 \
        curl \
        udev \
        wget \
        unzip \
        # Pacotes para NPU e GPU
        libdrm2 \
        libgbm1 \
        libegl1-mesa \
        libgles2-mesa \
        mesa-utils \
        file \
        binutils \
        # Pacotes para câmera V4L2
        usbutils \
        v4l-utils \
        libv4l-dev && \
    rm -rf /var/lib/apt/lists/*

## Install TF Lite ##
COPY --from=tflite-build /build /build
RUN cp -r /build/* /
RUN pip3 install --break-system-packages --no-cache-dir /tflite_runtime-*.whl && rm -rf *.whl

COPY --from=tflite-build /usr/include/ /usr/include/
RUN apt-get -y update && apt-get install -y \
    libovxlib

# Configurar locale
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8

# Criar diretório da aplicação
WORKDIR /app

# Copiar requirements primeiro para cache eficiente
COPY requirements-gui.txt ./

# Criar e ativar ambiente virtual
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Instalar dependências Python básicas
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Instalar dependências base
RUN pip install --no-cache-dir -r requirements-gui.txt

# Copiar código da aplicação
COPY src/ ./src/
COPY data/ ./data/

# Configurar variáveis de ambiente para GUI
ENV DISPLAY=:0
ENV WAYLAND_DISPLAY=wayland-1
ENV XDG_RUNTIME_DIR=/tmp
ENV XDG_SESSION_TYPE=wayland
ENV QT_QPA_PLATFORM=wayland
ENV GDK_BACKEND=wayland

# Configurações para NPU
ENV TF_CPP_MIN_LOG_LEVEL=2
ENV CORAL_ENABLE_EDGETPU=1
ENV NPU_AVAILABLE=1

# Configurar permissões para usuário torizon (já existe na imagem base)
RUN usermod -a -G video,audio,dialout,plugdev torizon

# Permissões para dispositivos (manter root também)
RUN usermod -a -G video,audio,dialout,plugdev root

# Script de entrada
COPY docker-entrypoint-gui.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Comando padrão
ENTRYPOINT ["/entrypoint.sh"]
CMD ["python3", "src/main.py"]