#\!/bin/bash
set -e

echo "Installing missing libraries..."
sudo apt-get update
sudo apt-get install -y \
  libevent-2.1-7 \
  libgtk-4-1 \
  libgraphene-1.0-0 \
  libxslt1.1 \
  libwoff1 \
  gstreamer1.0-gl \
  gstreamer1.0-plugins-bad \
  flite1-dev \
  libwebpdemux2 \
  libavif13 \
  libharfbuzz-icu0 \
  libenchant-2-2 \
  libsecret-1-0 \
  libhyphen0 \
  libmanette-0.2-0 \
  libgles2

echo "Libraries installed successfully\!"
