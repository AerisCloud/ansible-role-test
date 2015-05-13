IMAGE=aeriscloud/ansible-ubuntu
TAGS=14.04 trusty lts

.PHONY: all

all: $(TAGS)

$(TAGS):
	docker build -t $(IMAGE):$@ .
