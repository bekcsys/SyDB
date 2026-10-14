# Docker image

`make start` and `make rebuild` build the image on this machine. Postgres data stays in its volume across a rebuild.

The image name and tag used when publishing are `DOCKER_IMAGE_WEBAPP` and `DOCKER_TAG` in `.env`.

## Publish

```bash
export DOCKERHUB_USER=your-dockerhub-user
export DOCKER_TAG=tagname
make docker-publish
```

`make docker-publish` builds and pushes. `make docker-build` and `make docker-push` are the two steps on their own.

## Stop

```bash
make stop
```
