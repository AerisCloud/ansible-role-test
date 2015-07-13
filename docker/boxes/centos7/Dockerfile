# This Dockerfile creates a provisionable image of CentOS 7 for use with ansible

FROM centos:7
MAINTAINER Christophe Robin <crobin@nekoo.com>

# Updating container (recommended by image provider)
# Also provide some default packages
RUN yum -y update && yum install -y dbus tar

# Change root password to ansible
RUN usermod --password XT7/q1XkHlXSs root

# Create ansible user
RUN useradd --password XT7/q1XkHlXSs --create-home --groups users,wheel ansible

# Setup sudo
RUN yum -y install sudo
RUN echo 'ansible	ALL=(ALL)	NOPASSWD: ALL' >> /etc/sudoers

# Install sshd and generate ssh keys
RUN yum -y install openssh-server
RUN sshd-keygen || true
RUN systemctl enable sshd

# Cleanup
RUN yum clean all

# Used by systemd
VOLUME /sys/fs/cgroup

# Expose SSH
EXPOSE 22
CMD ["/sbin/init"]
