IMAGE=aeriscloud/ansible-debian
TAGS=7 wheezy

.PHONY: all

all: $(TAGS)

$(TAGS):
	docker build -t $(IMAGE):$@ .
