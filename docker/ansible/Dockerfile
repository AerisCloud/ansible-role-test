FROM python:2.7

RUN pip install ansible
RUN apt-get update && apt-get install sshpass && rm -Rf /var/cache/apt /var/lib/apt/lists
RUN echo "[defaults]\nhost_key_checking = False" > ~/.ansible.cfg
RUN mkdir ~/.ssh && echo "Host github.com\n\tStrictHostKeyChecking no\n" > ~/.ssh/config
RUN mkdir -p /etc/ansible/plugins/callback_plugins
ADD https://raw.githubusercontent.com/AerisCloud/ansible-receipts/master/receipts.py /etc/ansible/plugins/callback_plugins/receipts.py

ENV ANSIBLE_CALLBACK_PLUGINS /etc/ansible/plugins/callback_plugins

CMD /bin/bash
