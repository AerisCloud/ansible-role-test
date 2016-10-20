# This Dockerfile creates a provisionable image of CentOS 7 for use with ansible

FROM centos:7
MAINTAINER Christophe Robin <crobin@nekoo.com>

# Enable systemd
ENV container docker
RUN (cd /lib/systemd/system/sysinit.target.wants/; \
for i in *; do [ $i == systemd-tmpfiles-setup.service ] || rm -f $i; done); \
rm -f /lib/systemd/system/multi-user.target.wants/*;\
rm -f /etc/systemd/system/*.wants/*;\
rm -f /lib/systemd/system/local-fs.target.wants/*; \
rm -f /lib/systemd/system/sockets.target.wants/*udev*; \
rm -f /lib/systemd/system/sockets.target.wants/*initctl*; \
rm -f /lib/systemd/system/basic.target.wants/*;\
rm -f /lib/systemd/system/anaconda.target.wants/*;
VOLUME [ "/sys/fs/cgroup"  ]

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

# Allow sshing in
RUN sed -i 's/^UsePrivilegeSeparation.*/UsePrivilegeSeparation no/' /etc/ssh/sshd_config

# Used by systemd
VOLUME /sys/fs/cgroup

# Expose SSH
EXPOSE 22

CMD ["/usr/sbin/init"]
