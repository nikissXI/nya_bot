#!/bin/bash

# 开启ipv4转发
sudo sed -i 's/.*net.ipv4.ip_forward.*/net.ipv4.ip_forward=1/' /etc/sysctl.conf
sudo sysctl -p /etc/sysctl.conf

# 判断文件夹是否存在
if [ ! -d "tunnel/prikey" ]; then
sudo mkdir -p tunnel/prikey
fi

if [ ! -d "tunnel/pubkey" ]; then
sudo mkdir -p tunnel/pubkey
fi

if [ ! -d "tunnel/conf" ]; then
sudo mkdir -p tunnel/conf
fi

if [ ! -d "data" ]; then
sudo mkdir -p data
fi

if [ ! -d "log/bd_log" ]; then
sudo mkdir -p log/bd_log
fi

if [ ! -d "log/room_log" ]; then
sudo mkdir -p log/room_log
fi

if [ ! -d "log/ip_log" ]; then
sudo mkdir -p log/ip_log
fi

if [ ! -e "/etc/wireguard/miao.conf" ]; then
echo "[Interface]
ListenPort = ${2}
PrivateKey = 4ALX5mWGOPsyQKvaGvMfdZ071xTvDskPNpB7iUQdN3E=" > /etc/wireguard/miao.conf
fi

sudo wg-quick up miao
sudo ip addr add ${1}/16 dev miao
