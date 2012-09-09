LESS_FILES= $(shell find static -name '*.less')
BOOTSTRAP_FILES= $(shell find static -name 'bootstrap.less')
CSS_FILES=$(LESS_FILES:.less=.css)

all: less

bootstrap: $(BOOTSTRAP_FILES)

less: $(CSS_FILES) | bootstrap

%.css: %.less
    lessc $< > $@