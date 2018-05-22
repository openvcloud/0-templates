#!/bin/bash

function usage()
{
    echo "usage:"
    echo "   -h: listing  usage"
    echo "   -d: install requirements"
    echo "   -r: provide path for tests you want to run"
    echo "   -s: start zrobot server and connect to it"
    echo ""
}

while getopts r:dsh OPT
do
    case "$OPT" in
        h) usage
           exit;;
        d) DEP=True ;;
        r) TESTSPATH=$OPTARG ;;
        s) SERVER=True ;;
    esac
done

## Cloning the framework
git -C /tmp clone -b master https://github.com/0-complexity/G8_testing.git
cp -r /tmp/G8_testing/functional_testing/zrobot_templates/framework .
rm -rf /tmp/G8_testing

## Install requirements
if [ ${DEP} ]; then
  echo " "
  echo "* Installing requirements"
  pip3 install -r requirements.txt
fi

## Starting and connecting to zrobot server
if [ ${SERVER} ]; then
  echo "* Start zrobot server and connect to it"
  zrobot server start --listen 0.0.0.0:6600 --template-repo https://github.com/openvcloud/0-templates.git --data-repo https://github.com/john-kheir/0-robot6.git &> /dev/null &
  sleep 10
  ip=$(sudo zerotier-cli listnetworks | grep PRIVATE | awk '{print $9}' | cut -d '/' -f1)
  zrobot robot connect main http://$ip:6600
fi

## running testsuite
if [ ${TESTSPATH} ]; then
  echo " "
  echo "* Running Tests"
  nosetests -v -s ${TESTSPATH} --tc-file=config.ini
fi
