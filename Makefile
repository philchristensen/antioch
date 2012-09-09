LESS_FILES= $(shell find static -name '*.less')
CSS_FILES=$(LESS_FILES:.less=.css)

less: $(CSS_FILES)

%.css: %.less
    lessc $< > $@