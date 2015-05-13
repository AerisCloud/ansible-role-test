DOCKERFILES = $(shell find docker -name Makefile)
DOCKER = $(DOCKERFILES:/Makefile=) 

.PHONY: clean build all docker $(DOCKER)

all: dist

clean:
	rm -Rf venv ansibleroletest/*.pyc build dist ansible_role_test.egg-info ansible-role-test.spec

build: venv
	venv/bin/python setup.py install

# same as build but use symbolic links
dev: venv
	venv/bin/pip install -e .

dist: build venv/bin/pyinstaller
	venv/bin/pyinstaller --clean --onefile bin/ansible-role-test
	mv dist/ansible-role-test "dist/ansible-role-test-$(shell uname -s)-$(shell uname -m)"

venv:
	virtualenv2 venv

# pypi version is super old, use github version instead
venv/bin/pyinstaller:
	venv/bin/pip install git+https://github.com/pyinstaller/pyinstaller.git\#egg\=pyinstaller

# build the necessary docker images
docker: $(DOCKER)

$(DOCKER):
	make -C $@
