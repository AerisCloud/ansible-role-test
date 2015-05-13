IMAGE=aeriscloud/ansible-debian
TAGS=8 jessie latest

.PHONY: all

all: $(TAGS)

$(TAGS):
	docker build -t $(IMAGE):$@ .
