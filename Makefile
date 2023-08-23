# Makefile

# The default target if none is specified
.PHONY: all
all: test

export OPENAI_API_KEY

build:
	@docker build -t marbot .


test: build
	@docker run -e OPENAI_API_KEY -v $(CURDIR)/testdata:/app/testdata -it --rm marbot python3 -m unittest discover -s scripts -p '*_ut.py'

run: build
	@docker run -e OPENAI_API_KEY -v $(CURDIR)/testdata:/app/testdata -it --rm marbot python3 scripts/marbot.py
