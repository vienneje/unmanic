# Unit Testing



## Setup

Before any tests can be run, you need to execute
```
tests/scripts/setup_tests.sh
```


-----------------------------------------------------------


## Python PEP8 conformity

Prior to committing code, it should be tested against PEP8 formatting standards
```
pycodestyle ./
```

You can also specify the files to run individual. Eg.
```
pycodestyle ./lib/common.py
```


-----------------------------------------------------------


## Python unit tests

To run all tests execute from the project directory root:
```
pytest --log-cli-level=INFO
```

You can also specify the files to run individual. Eg.
```
pytest --log-cli-level=INFO lib/common.py
```

For more in-depth logging of tests, change the params to:
```
pytest --log-cli-level=DEBUG -s
```


-----------------------------------------------------------


## WebUI acceptance tests

This is still a WIP but the idea will be to have a series of API calls to determine successful functionality of the Web API

To run the test first run a docker environment. You can do this by running
```
tests/scripts/library_scan.sh
```
You can export the following variables to configure the test container:
```
DEBUGGING=true
NUMBER_OF_WORKERS=1
SCHEDULE_FULL_SCAN_MINUTES=1
RUN_FULL_SCAN_ON_START=true
```
To clean the config run 
```
tests/scripts/library_scan.sh --clean
```


-----------------------------------------------------------


## Python unit tests within docker

To run the python unit tests within the test docker env
(in order to test them in a controlled environment), run
these commands:

```
docker-compose -f docker/docker-compose-test.yml up --force-recreate
```

Wait for the container to start, then run:

```
docker exec --workdir=/app unmanic-testenv pycodestyle ./
```

and

```
docker exec --workdir=/app unmanic-testenv pytest --log-cli-level=INFO
```

When developing, if you wish to run only a single test, run:

```
docker exec --workdir=/app unmanic-testenv pytest --log-cli-level=INFO --maxfail 1 -s tests/test_<TEST NAME>.py
```
