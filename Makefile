DOCKER = $(patsubst %/Makefile,%,$(shell find docker -name Makefile -mindepth 2))
DOCKER_PULL = $(patsubst %,%-pull,$(DOCKER))
TARGET = "dist/ansible-role-test-$(shell uname -s)-$(shell uname -m)"

VIRTUALENV ?= virtualenv

.PHONY: clean build all docker docker-pull $(DOCKER) $(DOCKER_PULL)

all: dist

clean:
	rm -Rf venv ansibleroletest/*.pyc build dist ansible_role_test.egg-info ansible-role-test.spec

build: venv
	venv/bin/python setup.py install

# same as build but use symbolic links
dev: venv
	venv/bin/pip install --upgrade -e .

dist: $(TARGET)

$(TARGET): build venv/bin/pyinstaller
	venv/bin/pyinstaller --clean --onefile bin/ansible-role-test
	mv dist/ansible-role-test $(TARGET)

venv:
	$(VIRTUALENV) venv

# pypi version is super old, use github version instead
venv/bin/pyinstaller:
	venv/bin/pip install git+https://github.com/pyinstaller/pyinstaller.git\#egg\=pyinstaller

# build the necessary docker images
docker: $(DOCKER)

docker-pull: $(DOCKER_PULL)

$(DOCKER):
	make -C $@

$(DOCKER_PULL):
	make -C $(patsubst %-pull,%,$@) pull
