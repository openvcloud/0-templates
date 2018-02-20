all: test

test:
	pytest --cov=./ templates

test-ui:
	pytest --cov=./ --cov-report=html templates
