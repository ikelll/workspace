FROM debian:bookworm-slim

WORKDIR /opt/build
COPY . .
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip python3 python3-venv python3-dev \
    build-essential patchelf libkrb5-dev \
    libglib2.0-0 libbrotli1 \
    make ruby \
 && rm -rf /var/lib/apt/lists/*
#spice build package
RUN apt-get update && apt-get install -y \
    vim zip make rpm rsync ruby meson ninja-build gcc g++ pkg-config libtool \
    libglib2.0-dev libusb-1.0-0-dev \
    meson ninja-build pkg-config cmake curl unzip \
    libusb-1.0-0-dev libglib2.0-dev libpixman-1-dev \
    libssl-dev libjpeg-dev zlib1g-dev libjson-glib-dev \
    libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev \
    gstreamer1.0-pulseaudio gstreamer1.0-qt6 \
    gstreamer1.0-vaapi gstreamer1.0-x \
    gstreamer1.0-plugins-bad gstreamer1.0-plugins-bad-apps \
    libcap-ng0 libpolkit-gobject-1-dev libcap-ng-dev libacl1-dev libgirepository1.0-dev libcap-ng-dev libphodav-3.0-dev \
    gstreamer1.0-gtk3 gstreamer1.0-libcamera \
    gstreamer1.0-libav gstreamer1.0-alsa \
    libopus-dev liblz4-dev libsasl2-dev libcacard-dev \
    libgtk-3-dev python3.11-venv python3-pip \
    gettext \
    && rm -rf /var/lib/apt/lists/*

RUN gem install fpm
RUN python3 -m venv venv 
RUN /opt/build/venv/bin/pip install -U pip setuptools wheel
RUN /opt/build/venv/bin/pip install -r requirements.txt
RUN /opt/build/venv/bin/pip install pyparsing PySide6 Nuitka ordered-set zstandard pyspnego krb5

RUN /opt/build/venv/bin/python --version
RUN /opt/build/venv/bin/pip list
ENV PATH="/opt/build/venv/bin:$PATH"
ENV VIRTUAL_ENV="/opt/build/venv"
RUN chmod +x rebuild.sh
RUN ./rebuild.sh
RUN mkdir dist-linux
RUN mkdir /opt/spice
