# Get list of less, with paths
LESS_FILES= $(shell find $(SOURCEDIR) -name '*.less')
CSS_FILES=$(LESS_FILES:.less=.css)

less: $(CSS_FILES)

%.css: %.less
    lessc $< > $@