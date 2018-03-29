#!/bin/bash

# This script is used when using travis to run the testsuite
echo "[+] Installing zerotier"
curl -s https://install.zerotier.com/ | sudo bash

echo "[+] Joining zerotier network : ${zerotier_network}"
sudo zerotier-cli join ${zerotier_network}; sleep 10

echo "[+] Authorizing zerotier member"
memberid=$(sudo zerotier-cli info | awk '{print $3}')
curl -s -H "Content-Type: application/json" -H "Authorization: Bearer ${zerotier_token}" -X POST -d '{"config": {"authorized": true}}' https://my.zerotier.com/api/network/${zerotier_network}/member/${memberid} > /dev/null

for i in {1..20}; do
    ping -c1 ${ctrl_zt_ipaddress} > /dev/null && break
done

if [ $? -gt 0 ]; then
    echo "Can't reach the controller using this ip address ${ctrl_zt_ipaddress}"; exit 1
fi

sudo echo "${ctrl_zt_ipaddress}  ${environment}" >> /etc/hosts
