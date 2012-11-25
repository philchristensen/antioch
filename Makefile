BOOTSTRAP_FILES= $(shell find . -name 'bootstrap.less' -or -name 'responsive.less')
LESS_FILES= $(shell find . -name '*.less' -and -not -path '*src*')

all: staticdir bootstrap less

staticdir:
	python manage.py collectstatic static

bootstrap: $(BOOTSTRAP_FILES:.less=.css)

less: $(LESS_FILES:.less=.css)

%.css: %.less
	lessc $< > $@
