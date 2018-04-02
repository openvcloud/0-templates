#!/bin/bash
# This script is used when using travis to run the testsuite
action=$1

if [[ ${action} == "before" ]]; then
    echo "[+] Generating ssh key ..."
    ssh-keygen -f ~/.ssh/id_rsa -P ''

    echo "[+] Creating packet machine ..."
    python3 packet.py -a create_machine -t ${packet_token} -k ${TRAVIS_JOB_NUMBER}

    echo "[+] Sending setup script to packet machine ..."
    ctrl_ipaddress=$(cat /tmp/device_ipaddress.txt)
    scp -o StrictHostKeyChecking=no packet_setup.sh root@${ctrl_ipaddress}:/root/
    ssh -t -o StrictHostKeyChecking=no root@${ctrl_ipaddress} "bash packet_setup.sh ${ovc_templates_branch} ${js9_branch} ${zrobot_branch} ${zerotier_network} ${zerotier_token} ${ctrl_zt_ipaddress} ${environment}"
    scp -o StrictHostKeyChecking=no prepare.sh root@${ctrl_ipaddress}:/root/

elif [[ ${action} == "run" ]]; then
    ssh -t -o StrictHostKeyChecking=no root@${ctrl_ipaddress} "bash prepare.sh -d -s -r testsuite/ovc_tests/a_basic/accounts_tests.py"

elif [[ ${action} == "teardown" ]]; then
    echo "[+] Deleting packet machine ..."
    python3 packet.py -a delete_machine -t ${packet_token} -k ${TRAVIS_JOB_NUMBER}

fi
