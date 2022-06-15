#!/bin/bash
eth_dev=eth0
RXpre=$(cat /proc/net/dev | grep $eth_dev | tr : " " | awk '{print $2}')
TXpre=$(cat /proc/net/dev | grep $eth_dev | tr : " " | awk '{print $10}')
sleep 1
RXnext=$(cat /proc/net/dev | grep $eth_dev | tr : " " | awk '{print $2}')
TXnext=$(cat /proc/net/dev | grep $eth_dev | tr : " " | awk '{print $10}')
RX=$((${RXnext}-${RXpre}))
TX=$((${TXnext}-${TXpre}))
RX=$(echo $RX | awk '{print $1/1024}')
TX=$(echo $TX | awk '{print $1/1024}')
echo -e "$RX $TX"