.PHONY: clean build all docker

all: dist

clean:
	rm -Rf venv ansibleroletest/*.pyc build dist ansible_role_test.egg-info ansible-role-test.spec

build: venv
	venv/bin/python setup.py install

dist: build venv/bin/pyinstaller
	venv/bin/pyinstaller --clean --onefile bin/ansible-role-test
	mv dist/ansible-role-test "dist/ansible-role-test-$(shell uname -s)-$(shell uname -m)"

venv:
	virtualenv2 venv

venv/bin/pyinstaller:
	venv/bin/pip install git+https://github.com/pyinstaller/pyinstaller.git\#egg\=pyinstaller

docker:
	cd docker/ansible && docker build -t aeriscloud/ansible:latest .
	cd docker/boxes/centos6 && docker build -t aeriscloud/ansible-centos:6 .
	cd docker/boxes/centos7 && docker build -t aeriscloud/ansible-centos:7 .
