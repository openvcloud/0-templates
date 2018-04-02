export LANGUAGE=en_US.UTF-8
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8
export LC_TYPE=en_US.UTF-8

js9_branch=${1}
zrobot_branch=${2}
zerotier_network=${3}
zerotier_token=${4}
ctrl_zt_ipaddress=${5}
environment=${6}

echo "[+] Installing requirements"
apt update
#install python packages
apt install git python3-pip python-pip -y
apt install python-dev python3-dev libffi-dev build-essential libssl-dev libxml2-dev libxslt1-dev zlib1g-dev -y
pip3 install python-dateutil requests zerotier git+https://github.com/gigforks/packet-python.git
echo "[+] Installing zerotier"
curl -s https://install.zerotier.com/ | sudo bash

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
sudo echo "${ctrl_zt_ipaddress}  ${environment}" >> /etc/hosts


echo "[+] Cloning 0-template repo"
git clone -b master https://github.com/openvcloud/0-templates

echo "[+] Installing Jumpscale9"
0-templates/utils/jumspcale_install.sh ${js9_branch}

echo "[+] Installing 0-robot"
0-templates/utils/zrobot_install.sh ${zrobot_branch}
