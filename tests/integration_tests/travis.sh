#!/bin/bash
# This script is used when using travis to run the testsuite
action=$1

if [[ ${action} == "setup" ]]; then

    echo "[+] Joining zerotier network: ${zerotier_network}"
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
    sudo chown -R travis:travis /etc/hosts
    sudo chown -R travis:travis /root
    sleep 1
    sudo echo \ >> /etc/hosts
    sudo echo "${ctrl_zt_ipaddress}  ${environment}" >> /etc/hosts

    while true; do
        ip=$(sudo zerotier-cli listnetworks | grep ${zerotier_network} | awk '{print $8}')
        if [[ $ip == '-' ]]; then
            sleep 5
        else
            break
        fi
    done

    for interface in $(ls /sys/class/net | grep zt); do
        sudo ifconfig ${interface} mtu 1280
    done

elif [[ ${action} == "run" ]]; then
    source prepare.sh -d -s -r testsuite/ovc_tests/a_basic/accounts_tests.py

fi
