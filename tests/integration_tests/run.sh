#!/bin/bash

## Cloning the framework
git -C /tmp clone -b master https://github.com/0-complexity/G8_testing.git
cp -r /tmp/G8_testing/functional_testing/zrobot_templates/framework .
rm -rf /tmp/G8_testing

## running testsuite
nosetests -v -s testsuite --tc-file=config.ini
