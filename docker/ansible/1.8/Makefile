IMAGE=aeriscloud/ansible
TAGS=1.8

.PHONY: all

all: $(TAGS)

$(TAGS):
	docker build -t $(IMAGE):$@ .
