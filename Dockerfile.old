# ARGUMENTS --------------------------------------------------------------------
##
# Board architecture
##
ARG IMAGE_ARCH=arm64

##
# Base container version
##
ARG BASE_VERSION=4

##
# Directory of the application inside container
##
ARG APP_ROOT=

FROM --platform=linux/${IMAGE_ARCH} \
    torizon/debian:${BASE_VERSION} AS deploy

ARG IMAGE_ARCH
ARG APP_ROOT

# Make sure we don't get notifications we can't answer during building.
ENV DEBIAN_FRONTEND="noninteractive"

# Configure apt to handle repository issues
RUN echo 'APT::Get::Assume-Yes "true";' >> /etc/apt/apt.conf.d/90assumeyes && \
    echo 'APT::Get::Fix-Broken "true";' >> /etc/apt/apt.conf.d/90fixbroken && \
    echo 'APT::Install-Recommends "false";' >> /etc/apt/apt.conf.d/90norecommends

# Update package lists and install base packages
RUN apt update --fix-missing -q -y || apt update -q -y

# Install required packages
RUN apt install -q -y \
    ca-certificates \
    apt-transport-https \
    software-properties-common \
    && apt update -q -y && \
    apt install -q -y \
    python3-minimal \
    python3-pip \
    python3-venv \
    python3-tk \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libgstreamer1.0-0 \
    libgstreamer-plugins-base1.0-0 \
    libgtk-3-0 \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    qtwayland5 \
    curl \
    gnupg \
    lsb-release \
    libusb-1.0-0 \
    udev \
# DO NOT REMOVE THIS LABEL: this is used for VS Code automation
    # __torizon_packages_prod_start__
    # __torizon_packages_prod_end__
# DO NOT REMOVE THIS LABEL: this is used for VS Code automation
    && apt clean && apt autoremove && \
    rm -rf /var/lib/apt/lists/*

# Install Edge TPU runtime for NPU support on IMX8MP
RUN echo "deb https://packages.cloud.google.com/apt coral-edgetpu-stable main" | tee /etc/apt/sources.list.d/coral-edgetpu.list && \
    curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /usr/share/keyrings/coral-edgetpu-archive-keyring.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/coral-edgetpu-archive-keyring.gpg] https://packages.cloud.google.com/apt coral-edgetpu-stable main" | tee /etc/apt/sources.list.d/coral-edgetpu.list && \
    apt update && \
    apt install -y libedgetpu1-std && \
    apt clean && apt autoremove && \
    rm -rf /var/lib/apt/lists/*

# Create virtualenv
RUN python3 -m venv ${APP_ROOT}/.venv --system-site-packages

# Install pip packages on venv
COPY requirements-release.txt /requirements-release.txt
RUN . ${APP_ROOT}/.venv/bin/activate && \
    pip3 install --upgrade pip && pip3 install -r requirements-release.txt && \
    rm requirements-release.txt

# Copy the application source code in the workspace to the $APP_ROOT directory
# path inside the container, where $APP_ROOT is the torizon_app_root
# configuration defined in settings.json
COPY ./src ${APP_ROOT}/src
COPY data/ ${APP_ROOT}/data/

WORKDIR ${APP_ROOT}
ENV APP_ROOT=${APP_ROOT}

# Activate and run the code
CMD ["/bin/sh", "-c", ". ${APP_ROOT}/.venv/bin/activate && python3 -u src/main.py"]
