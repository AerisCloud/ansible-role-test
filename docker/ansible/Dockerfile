FROM python:2.7

RUN pip install ansible
RUN apt-get update && apt-get install sshpass && rm -rf /var/cache/apt /var/lib/apt/lists
RUN echo "[defaults]\nhost_key_checking = False" > ~/.ansible.cfg
RUN mkdir ~/.ssh && echo "Host github.com\n\tStrictHostKeyChecking no\n" > ~/.ssh/config

CMD /bin/bash