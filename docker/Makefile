include meta

TAGS_PULL = $(patsubst %,%-pull,$(TAGS))

.PHONY: all pull $(TAGS) $(TAGS_PULL)

all: $(TAGS)

pull: $(TAGS_PULL)

$(TAGS):
	docker build -t $(IMAGE):$@ .

$(TAGS_PULL):
	docker pull $(IMAGE):$(patsubst %-pull,%,$@)
