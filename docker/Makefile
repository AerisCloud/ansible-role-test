include meta

DOCKER_OPTS ?= 
TAGS_PULL = $(patsubst %,%-pull,$(TAGS))

.PHONY: all pull $(TAGS) $(TAGS_PULL)

all: $(TAGS)

pull: $(TAGS_PULL)

$(TAGS):
	docker build $(DOCKER_OPTS) -t $(IMAGE):$@ .

$(TAGS_PULL):
	docker pull $(IMAGE):$(patsubst %-pull,%,$@)
