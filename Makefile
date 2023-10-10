.PHONY: nightly

all: build eval

eval:
	python3 python/national_geographic.py

build:
	python3 python/build.py

nightly: clean
	python3 python/build.py nightly
	python3 python/nightly.py

clean:
	rm -rf _build third_party log out
