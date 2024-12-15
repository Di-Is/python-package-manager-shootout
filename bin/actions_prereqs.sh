#!/bin/bash
set -euf -o pipefail

# sentry dependencies
sudo apt-get update -qq
sudo apt-get install -y libxmlsec1-dev librdkafka-dev
wget https://github.com/sharkdp/hyperfine/releases/download/v1.19.0/hyperfine_1.19.0_amd64.deb
sudo dpkg -i hyperfine_1.19.0_amd64.deb
# benchmark setup
pip --disable-pip-version-check --no-cache-dir install csv2md
mkdir -p timings
make requirements.txt
