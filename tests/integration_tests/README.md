
## Steps needed for running the testsuite

1- Install [ZROBOT](https://github.com/Jumpscale/0-robot/blob/master/docs/getting_started.md).
 
2- Change ```config.ini``` as needed.
```
cd /tests/integration_tests
vim config.ini
```

3- Install requirements.
```
cd /tests/integration_tests
pip3 install -r requirements
```
   
4- Run ```prepare.sh``` to clone the framework needed for running the tests.
```
cd /tests/integration_tests
bash prepare.sh
```
   
5- Running Tests
```
cd /tests/integration_tests
nosetests -v -s testsuite --tc-file=config.ini
```
## Note
Stesps 3, 4 and 5 can be replaced by only one step
```
cd /tests/integration_tests
bash run -d -r testsuite
```
In which
```
bash prepare.sh -h
usage:
   -h: listing  usage
   -d: install requirements
   -r: provide path for tests you want to run
```
