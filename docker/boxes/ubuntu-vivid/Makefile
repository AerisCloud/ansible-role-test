IMAGE=aeriscloud/ansible-ubuntu
TAGS=15.04 vivid latest

.PHONY: all

all: $(TAGS)

$(TAGS):
	docker build -t $(IMAGE):$@ .
