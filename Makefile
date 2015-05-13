.PHONY: clean build all docker

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
docker: docker-ansible docker-centos6 docker-centos7 docker-debian-wheezy docker-debian-jessie

# TODO: maybe move those to dedicated makefiles
docker-ansible:
	cd docker/ansible && docker build -t aeriscloud/ansible:latest .

docker-centos6:
	cd docker/boxes/centos6 && docker build -t aeriscloud/ansible-centos:6 .

docker-centos7:
	cd docker/boxes/centos7 && docker build -t aeriscloud/ansible-centos:7 .
	cd docker/boxes/centos7 && docker build -t aeriscloud/ansible-centos:latest .

docker-debian-wheezy:
	cd docker/boxes/debian-wheezy && docker build -t aeriscloud/ansible-debian:wheezy .

docker-debian-jessie:
	cd docker/boxes/debian-jessie && docker build -t aeriscloud/ansible-debian:jessie .
	cd docker/boxes/debian-jessie && docker build -t aeriscloud/ansible-debian:latest .