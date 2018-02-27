all: test

test:
	pytest --cov=./ -v templates

test-ui:
	pytest --cov=./ --cov-report=html -v templates
