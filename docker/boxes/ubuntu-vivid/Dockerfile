# This Dockerfile creates a provisionable image of Debian Wheezy for use with ansible-role-test

FROM ubuntu:vivid
MAINTAINER Christophe Robin <crobin@nekoo.com>

# Updating container (recommended by image provider)
RUN apt-get update && apt-get upgrade -y

# Change root password to ansible
RUN usermod --password XT7/q1XkHlXSs root

# Create ansible user
RUN useradd --password XT7/q1XkHlXSs --create-home --groups users ansible

# Install python for ansible
RUN apt-get install -y python

# Setup sudo
RUN apt-get install -y sudo
RUN echo 'ansible	ALL=(ALL)	NOPASSWD: ALL' >> /etc/sudoers

# Install sshd, do a test run
RUN apt-get install -y openssh-server
RUN /etc/init.d/ssh start && /etc/init.d/ssh stop

# Cleanup
RUN apt-get clean

# Cache some folders
VOLUME /var/cache/apt
VOLUME /var/lib/apt

# Expose SSH
EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]
