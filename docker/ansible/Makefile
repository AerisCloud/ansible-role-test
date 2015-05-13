IMAGE=aeriscloud/ansible
TAGS=latest

.PHONY: all

all: $(TAGS)

$(TAGS):
	docker build -t $(IMAGE):$@ .
