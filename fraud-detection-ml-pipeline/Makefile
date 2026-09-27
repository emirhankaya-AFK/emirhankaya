.PHONY: install train test run
install:
	pip install -r requirements-dev.txt
train:
	python -m src.train
test:
	pytest -q
run:
	uvicorn src.api:app --reload

