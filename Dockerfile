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

RUN apt-get -q -y update && apt-get -q -y install --no-install-recommends \
    python3-minimal python3-pip python3-venv libgl1 libglib2.0-0 libxext6 libxrender1 \
    libxcb-xinerama0 libxcb-cursor0 python3-setuptools python3-wheel python3-tk \
    python3-pil python3-pil.imagetk pkg-config libhdf5-dev libatlas-base-dev libopenblas-dev \
    liblapack-dev libcurl4-openssl-dev libfreetype6-dev libpng-dev libtiff5-dev libjpeg-dev \
    libwebp-dev tcl8.6-dev tk8.6-dev ffmpeg libsm6 libxrender-dev libgl1-mesa-glx libgtk-3-0 \
    libgdk-pixbuf2.0-0 libxss1 curl udev wget unzip libdrm2 libgbm1 libegl1-mesa libgles2-mesa \
    mesa-utils file binutils usbutils v4l-utils libv4l-dev \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get -y update && apt-get install -y libovxlib || true

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8

WORKDIR /app
COPY requirements-gui.txt ./
COPY src/ ./src/
COPY data/ ./data/
COPY docker-entrypoint-gui.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# --------------------
# Stage: final
# --------------------
FROM base AS final

# Copy artefacts built in tflite-build
COPY --from=tflite-build /usr/lib/ /usr/lib/
COPY --from=tflite-build /build /build
RUN cp -r /build/* /

COPY --from=tflite-build /usr/include/ /usr/include/
RUN apt-get -y update && apt-get install -y \
    libovxlib

# Create virtualenv and install Python deps
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install Python dependencies with better error handling
RUN pip install --no-cache-dir -r requirements-gui.txt

# Ensure TensorFlow Lite libraries are accessible
ENV LD_LIBRARY_PATH="/opt/venv/lib/python3.11/site-packages/tflite_runtime:/usr/lib:/usr/local/lib:${LD_LIBRARY_PATH}"
ENV PYTHONPATH="/opt/venv/lib/python3.11/site-packages:${PYTHONPATH}"

# GUI / NPU env
ENV DISPLAY=:0
ENV WAYLAND_DISPLAY=wayland-1
ENV XDG_RUNTIME_DIR=/tmp
ENV XDG_SESSION_TYPE=wayland
ENV QT_QPA_PLATFORM=wayland
ENV GDK_BACKEND=wayland
ENV TF_CPP_MIN_LOG_LEVEL=2
ENV CORAL_ENABLE_EDGETPU=1
ENV NPU_AVAILABLE=1

RUN usermod -a -G video,audio,dialout,plugdev torizon || true
RUN usermod -a -G video,audio,dialout,plugdev root || true

ENTRYPOINT ["/entrypoint.sh"]
CMD ["python3", "src/main.py"]

