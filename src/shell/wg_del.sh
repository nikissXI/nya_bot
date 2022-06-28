#!/bin/bash

if [ -e "tunnel/conf/${1}.conf" ]; then
sudo rm -rf tunnel/conf/${1}.conf
sudo rm -rf tunnel/prikey/${1}_prikey
sudo rm -rf tunnel/pubkey/${1}_pubkey
fi
