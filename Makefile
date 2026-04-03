.PHONY: setup evolve arena dashboard test data clean

setup:
	pip install -r requirements.txt

data:
	python -m darwinia.utils.data_loader --download btc_1h --output data/

evolve:
	python -m darwinia.evolution.engine --generations $(or $(GENERATIONS),50) --population 50 --output output/

arena:
	python examples/run_arena.py

dashboard:
	streamlit run dashboard/app.py

test:
	python -m pytest tests/ -v

clean:
	rm -rf output/*
