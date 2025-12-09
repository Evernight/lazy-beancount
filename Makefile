lock:
	pip lock -r requirements.txt

docker-build:
	docker buildx build --platform linux/amd64,linux/arm64 -t vandereer/lazy-beancount:latest . --target=regular
	docker buildx build --platform linux/amd64,linux/arm64 -t vandereer/lazy-beancount:extra . --target=extra