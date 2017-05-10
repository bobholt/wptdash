#!/bin/sh
apt-get update
apt install libssl-dev -y
apt install python3 -y
apt install python3-dev -y
apt install python3-pip -y
pip3 install --upgrade pip
pip3 install ansible
pip3 install virtualenv
