#!/bin/bash
# This script is used when using travis to run the testsuite
action=$1

if [[ ${action} == "before" ]]; then
    echo "[+] Generating ssh key ..."
    ssh-keygen -f ~/.ssh/id_rsa -P ''

    echo "[+] Creating packet machine ..."
    python3 packet_script.py -a create_machine -t ${packet_token} -k ${TRAVIS_JOB_NUMBER}

    echo "[+] Sending setup script to packet machine ..."
    ctrl_ipaddress=$(cat /tmp/device_ipaddress.txt)
    scp -o StrictHostKeyChecking=no packet_setup.sh root@${ctrl_ipaddress}:/root/
    ssh -t -o StrictHostKeyChecking=no root@${ctrl_ipaddress} "bash packet_setup.sh ${js9_branch} ${zrobot_branch} ${zerotier_network} ${zerotier_token} ${ctrl_zt_ipaddress} ${environment}"

elif [[ ${action} == "run" ]]; then
    ctrl_ipaddress=$(cat /tmp/device_ipaddress.txt)
    ssh -t -o StrictHostKeyChecking=no root@${ctrl_ipaddress} "export IYO_SECRET=${IYO_SECRET}"
    ssh -t -o StrictHostKeyChecking=no root@${ctrl_ipaddress} "cd 0-templates/tests/integration_tests; bash prepare.sh -d -s -r testsuite/ovc_tests/a_basic/accounts_tests.py"

elif [[ ${action} == "teardown" ]]; then
    echo "[+] Deleting packet machine ..."
    python3 packet_script.py -a delete_machine -t ${packet_token} -k ${TRAVIS_JOB_NUMBER}

fi
