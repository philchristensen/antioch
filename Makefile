LESS_FILES= $(shell find static/less -name '*.less')
BOOTSTRAP_FILES= $(shell find static/bootstrap -name 'bootstrap.less')

all: bootstrap less

bootstrap: $(BOOTSTRAP_FILES:.less=.css)

less: $(LESS_FILES:.less=.css)

%.css: %.less
	lessc $< > $@