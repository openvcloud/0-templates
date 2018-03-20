#!/bin/bash

## Cloning the framework
git clone -C /tmp -b master https://github.com/0-complexity/G8_testing.git
cp -r /tmp/G8_testing/functional_testing/zrobot_templates/framework .


## running testsuite
nosetests -v -s testsuite --tc-file=config.ini

