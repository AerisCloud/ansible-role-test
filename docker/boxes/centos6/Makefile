IMAGE=aeriscloud/ansible-centos
TAGS=6

.PHONY: all

all: $(TAGS)

$(TAGS):
	docker build -t $(IMAGE):$@ .
