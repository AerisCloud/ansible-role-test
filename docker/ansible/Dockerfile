FROM ubuntu

RUN apt-get update \
    && apt-get install -y python \
                          python-dev \
                          python-setuptools \
                          python-pip \
                          python-virtualenv \
                          sshpass \
                          git \
    && rm -rf /var/cache/apt/* /var/lib/apt/lists/*
RUN pip install ansible
RUN echo "[defaults]\nhost_key_checking = False" > ~/.ansible.cfg
RUN mkdir ~/.ssh && echo "Host github.com\n\tStrictHostKeyChecking no\n" > ~/.ssh/config
RUN mkdir -p /etc/ansible/plugins/callback_plugins
ADD https://raw.githubusercontent.com/AerisCloud/ansible-receipts/master/receipts.py /etc/ansible/plugins/callback_plugins/receipts.py

ENV ANSIBLE_CALLBACK_PLUGINS /etc/ansible/plugins/callback_plugins

CMD /bin/bash
