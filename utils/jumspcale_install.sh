#!/bin/bash
set -e

sudo chown $USER:$USER /opt/
sudo chown -R $USER:$USER /usr/local

# settings
export BRANCH="development"

mkdir -p /opt/code/github/jumpscale
pushd /opt/code/github/jumpscale


# cloning source code
for target in core9 lib9 prefab9; do
    git clone --depth=1 -b ${BRANCH} https://github.com/jumpscale/${target}
done

# installing core and plugins
for target in core9 lib9 prefab9; do
    pushd ${target}
    pip3 install .
    popd
done

popd

# create ssh key for jumpscale config manager
mkdir -p ~/.ssh
ssh-keygen -f ~/.ssh/id_rsa -P ''
eval `ssh-agent -s`
ssh-add ~/.ssh/id_rsa

# initialize jumpscale config manager
mkdir -p /opt/code/config_test
git init /opt/code/config_test
touch /opt/code/config_test/.jsconfig