IMAGE=aeriscloud/ansible-centos
TAGS=7 latest

.PHONY: all

all: $(TAGS)

$(TAGS):
	docker build -t $(IMAGE):$@ .
