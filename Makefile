.PHONY: install test gateway ui eval audit clean help

help:
	@echo "ControlPlane.ai Commands"
	@echo ""
	@echo "make install     - Install dependencies"
	@echo "make test        - Run unit tests"
	@echo "make gateway     - Start FastAPI gateway on :8000"
	@echo "make ui          - Start Streamlit UI on :8501"
	@echo "make eval        - Run evaluation suite"
	@echo "make audit       - Verify audit chain"
	@echo "make clean       - Remove cache and temporary files"

install:
	pip install -r requirements.txt

test:
	pytest -v

gateway:
	uvicorn gateway.app:app --host 127.0.0.1 --port 8000 --reload

ui:
	streamlit run app.py

eval:
	python -m evaluation.run_eval

audit:
	python -m audit.verify

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".streamlit" -exec rm -rf {} +
