BOOTSTRAP_FILES= $(shell find static -name 'bootstrap.less' -or -name 'responsive.less')
LESS_FILES= $(shell find static/less -name '*.less')

all: bootstrap less

bootstrap: $(BOOTSTRAP_FILES:.less=.css)

less: $(LESS_FILES:.less=.css)

%.css: %.less
	lessc $< > $@