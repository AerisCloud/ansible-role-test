DOCKER = $(patsubst %/Makefile,%,$(shell find docker -mindepth 2 -name Makefile))
DOCKER_PULL = $(patsubst %,%-pull,$(DOCKER))
TARGET = "dist/ansible-role-test-$(shell uname -s)-$(shell uname -m)"

VIRTUALENV ?= virtualenv
PYTHON_ENV = $(shell test -d "venv" && echo "venv/bin/" || true)
PYTHON ?= python

.PHONY: clean build all docker docker-pull $(DOCKER) $(DOCKER_PULL)

all: dist

clean:
	rm -Rf venv ansibleroletest/*.pyc build dist ansible_role_test.egg-info ansible-role-test.spec

build:
	$(PYTHON_ENV)$(PYTHON) setup.py install

# same as build but use symbolic links
dev: venv
	venv/bin/pip install --upgrade -e .

dist: build $(TARGET)

$(TARGET): $(PYTHON_ENV)pyinstaller
	$(PYTHON_ENV)pyinstaller --clean --onefile bin/ansible-role-test -n $(TARGET)

venv:
	$(VIRTUALENV) --python=$(PYTHON) venv

# pypi version is super old, use github version instead
$(PYTHON_ENV)pyinstaller:
	$(PYTHON_ENV)pip install git+https://github.com/pyinstaller/pyinstaller.git\#egg\=pyinstaller

# build the necessary docker images
docker: $(DOCKER)

docker-pull: $(DOCKER_PULL)

$(DOCKER):
	make -C $@

$(DOCKER_PULL):
	make -C $(patsubst %-pull,%,$@) pull
