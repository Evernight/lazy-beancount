lock:
	pip lock -r requirements.txt

docker-build:
	docker buildx build --platform linux/amd64,linux/arm64 -t vandereer/lazy-beancount:latest . --target=regular
	docker buildx build --platform linux/amd64,linux/arm64 -t vandereer/lazy-beancount:extra . --target=extra

## Tests
test-js:
	cd tests; LANG=en npm run test

test-js-update:
	cd tests; LANG=en npm run test -- -u

test-js-ui:
	cd tests; LANG=en npm run test -- --ui

test: test-js

## Container
container-run: container-stop
	docker build -t lazy-beancount-test -f Dockerfile.test .
	docker run --user 0:0 -d --name lazy-beancount-test lazy-beancount-test
	docker exec lazy-beancount-test curl --retry 10 --retry-connrefused --silent --output /dev/null http://127.0.0.1:5000

container-stop:
	docker rm -f lazy-beancount-test

container-test: container-run
	docker exec lazy-beancount-test make test || (rm -rf ./tests/test-results && docker cp lazy-beancount-test:/usr/src/app/tests/test-results ./tests && exit 1)
	make container-stop

container-test-js-update: container-run
	docker exec lazy-beancount-test sh -c 'cd /usr/src/app/tests && LANG=en npx playwright test --update-snapshots $(if $(GREP),--grep "$(GREP)",)'
	docker cp lazy-beancount-test:/usr/src/app/tests/e2e/snapshots.test.ts-snapshots ./tests/e2e
	make container-stop