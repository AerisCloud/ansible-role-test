IMAGE=aeriscloud/ansible-ubuntu
TAGS=15.04 15 vivid latest

.PHONY: all

all: $(TAGS)

$(TAGS):
	docker build -t $(IMAGE):$@ .
