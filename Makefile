.PHONY: build run clean install

build:
	go build -o termnotes ./cmd/termnotes

run: build
	./termnotes

clean:
	rm -f termnotes

install:
	go install ./cmd/termnotes

test:
	go test ./...

fmt:
	go fmt ./...

vet:
	go vet ./...
