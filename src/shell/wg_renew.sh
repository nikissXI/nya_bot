#!/bin/bash

#保存配置
if [[ ${1} = "save" ]]; then

wg showconf miao > /etc/wireguard/miao.conf
exit

#重新载入配置
elif [[ ${1} = "readd" ]]; then

#获取原来的公钥并删除
OLDKEY=$(cat tunnel/pubkey/${2}_pubkey)
wg set miao peer ${OLDKEY} remove
#又加回去
wg set miao peer ${OLDKEY} allowed-ips ${2}/32
exit

#插入配置
elif [[ ${1} = "insert" ]]; then

#判断配置是否存在，存在就读取，不存在就创建
if [ -e "tunnel/pubkey/${5}_pubkey" ]; then

#读取公钥
PUBKEY=$(cat tunnel/pubkey/${5}_pubkey)
#插入公钥
wg set miao peer ${PUBKEY} allowed-ips ${5}/32
#退出
exit

fi

fi

# 刷新/生成配置
if [ -e "tunnel/conf/${5}.conf" ]; then

#获取原来的公钥并删除原配置
OLDKEY=$(cat tunnel/pubkey/${5}_pubkey)
wg set miao peer ${OLDKEY} remove

fi

# 生成私钥和公钥
PRK="tunnel/prikey/${5}_prikey"
PUK="tunnel/pubkey/${5}_pubkey"
wg genkey | tee ${PRK} | wg pubkey > ${PUK}
PRIKEY=$(cat ${PRK})
PUBKEY=$(cat ${PUK})
FILE="tunnel/conf/${5}.conf"

# 生成配置文件
echo "[Interface]
PrivateKey = ${PRIKEY}
Address = ${5}/16

[Peer]
PublicKey = qmcj4qqbR+bA5TBiSFG9tdGmAb4i7svKLfSKZILWfUI=
Endpoint = ${2}:${3}
AllowedIPs = ${4}.0.0/16
PersistentKeepalive = 30" > ${FILE}

# 生成配置二维码
qrencode -t PNG -o tunnel/png/${5}.png < ${FILE}

#把新配置写入wg
wg set miao peer ${PUBKEY} allowed-ips ${5}/32

if [[ ${1} = "renew" ]]; then
#把新配置写入wg本地配置文件
wg showconf miao > /etc/wireguard/miao.conf
fi
