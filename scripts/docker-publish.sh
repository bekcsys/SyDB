#!/usr/bin/env bash
# Build and push WebApp Django image to Docker Hub.
# Quick push: docker build -t becktkh/tempsensor-webapp:tagname . && docker push becktkh/tempsensor-webapp:tagname
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

: "${DOCKERHUB_USER:?Set DOCKERHUB_USER (your Docker Hub username)}"

IMAGE="${DOCKER_IMAGE_WEBAPP:-${DOCKERHUB_USER}/tempsensor-webapp}"
TAG="${DOCKER_TAG:-latest}"

echo "Building ${IMAGE}:${TAG} ..."
docker build -t "${IMAGE}:${TAG}" .

if [[ "${1:-}" == "--push" ]] || [[ "${PUSH:-}" == "1" ]]; then
  echo "Pushing ${IMAGE}:${TAG} ..."
  docker push "${IMAGE}:${TAG}"
  echo "Published ${IMAGE}:${TAG}"
else
  echo "Built ${IMAGE}:${TAG} (run with --push or PUSH=1 to publish)"
fi
