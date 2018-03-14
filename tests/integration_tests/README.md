
## Steps needed for running the testsuite

1- Install [ZROBOT](https://github.com/Jumpscale/0-robot/blob/master/docs/getting_started.md).

2- Install requirements.
   ```
   cd /tests/integration_tests
   pip3 install -r requirements 
   ```
3- Change ```config.ini``` as needed.
```
cd /tests/integration_tests
vim config.ini
```

4- Running Tests
```
cd /tests/integration_tests
nosetests -v -s testsuite --tc-file=config.ini
```
