# Makefile

# The default target if none is specified
.PHONY: all
all: test

export OPENAI_API_KEY
export GOOGLE_API_KEY

build:
	docker build -t marbot .

buildNotebook:
	docker build -f notebook/Dockerfile . -t marbot_notebook


test: build
	docker run -e OPENAI_API_KEY -v $(CURDIR)/testdata:/app/testdata -v $(CURDIR)/cachedata:/app/cachedata -it --rm marbot python3 -m unittest discover -s scripts -p '*_ut.py'

run: build
	docker run -e OPENAI_API_KEY -v $(CURDIR)/testdata:/app/testdata -v $(CURDIR)/cachedata:/app/cachedata -it --rm marbot python3 scripts/marbot.py

notebook: buildNotebook
	@echo Once this completes, open http://127.0.0.1:10000/lab/workspaces/auto-l in your browser
	docker run -p 10000:8888 -e OPENAI_API_KEY -e GOOGLE_API_KEY -v $(CURDIR)/testdata:/app/testdata -v $(CURDIR)/cachedata:/app/cachedata -v $(CURDIR)/scripts:/app/scripts marbot_notebook start-notebook.sh --IdentityProvider.token=''