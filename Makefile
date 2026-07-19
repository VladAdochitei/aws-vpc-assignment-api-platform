PYTHON_VERSION := 3.14
# must match terraform var.lambda_architecture
ARCH           ?= x86_64
BUILD_DIR      := build/package
SRC_DIR        := src
REQ_FILE       := requirements.txt

ifeq ($(ARCH),x86_64)
PIP_PLATFORM := manylinux2014_x86_64
else ifeq ($(ARCH),arm64)
PIP_PLATFORM := manylinux2014_aarch64
else
$(error Unsupported ARCH: $(ARCH))
endif

.PHONY: build clean

build: clean
	mkdir -p $(BUILD_DIR)
	pip install -r $(REQ_FILE) \
		-t $(BUILD_DIR) \
		--platform $(PIP_PLATFORM) \
		--python-version $(PYTHON_VERSION) \
		--only-binary=:all: \
		--upgrade
	cp -r $(SRC_DIR)/. $(BUILD_DIR)/

clean:
	rm -rf build