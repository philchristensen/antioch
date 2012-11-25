BOOTSTRAP_FILES= $(shell find static -name 'bootstrap.less' -or -name 'responsive.less')
LESS_FILES= $(shell find static/less -name '*.less')

LOCAL_BOOTSTRAP_FILES= $(shell find src -name 'bootstrap.less' -or -name 'responsive.less')
LOCAL_LESS_FILES= $(shell find src -name '*.less' -and -not -name 'bootstrap.less' -and -not -name 'responsive.less')

all: bootstrap less

bootstrap: $(BOOTSTRAP_FILES:.less=.css)

less: $(LESS_FILES:.less=.css)

local: bootstrap-local less-local

bootstrap-local: $(LOCAL_BOOTSTRAP_FILES:.less=.css)

less-local: $(LOCAL_LESS_FILES:.less=.css)

%.css: %.less
	lessc $< > $@