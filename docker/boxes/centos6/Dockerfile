# This Dockerfile creates a provisionable image of CentOS 6 for use with ansible

FROM centos:6
MAINTAINER Christophe Robin <crobin@nekoo.com>

# Updating container (recommended by image provider)
RUN yum -y update

# Change root password to ansible
RUN usermod --password XT7/q1XkHlXSs root

# Create ansible user
RUN useradd --password XT7/q1XkHlXSs --create-home --groups users,wheel ansible
#RUN mkdir /home/ansible/.ssh
#RUN chown ansible:ansible /home/ansible/.ssh
#RUN chmod 0700 /home/ansible/.ssh
#ADD insecure_key.pub /home/ansible/.ssh/authorized_keys
#RUN chown ansible:ansible /home/ansible/.ssh/authorized_keys
#RUN chmod 0600 /home/ansible/.ssh/authorized_keys

# Setup sudo
RUN yum -y install sudo
RUN echo 'ansible	ALL=(ALL)	NOPASSWD: ALL' >> /etc/sudoers

# Install sshd and generate ssh keys
RUN yum -y install openssh-server
RUN /etc/init.d/sshd start
RUN /etc/init.d/sshd stop

# Cleanup
RUN yum clean all

# Expose SSH
EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]
