include .env
export BACKEND_CONTAINER_NAME=sleekflow_backend
export BACKEND_IMAGE_NAME=sleekflow_backend
export DATABASE_CONTAINER_NAME=sleekflow_postgres
export DATABASE_IMAGE_NAME=postgres:15-bullseye
database-up:
	docker run -d --name ${DATABASE_CONTAINER_NAME} \
		--restart always \
		-p ${DATABASE_PORT}:5432 \
		--env POSTGRES_USER=${DATABASE_USER} \
		--env POSTGRES_PASSWORD=${DATABASE_PASSWORD} \
		--env POSTGRES_DB=${DATABASE_NAME} \
		${DATABASE_IMAGE_NAME}
database-down:
	docker stop ${DATABASE_CONTAINER_NAME} && docker rm ${DATABASE_CONTAINER_NAME}
backend-build:
	cd backend && docker build -t ${BACKEND_IMAGE_NAME} \
		--build-arg BACKEND_HOST=${BACKEND_HOST} \
		--build-arg BACKEND_PORT=${BACKEND_PORT} \
		--build-arg PROJECT_MODE=PRODUCTION \
		.
backend-up:
	docker run -d --name ${BACKEND_CONTAINER_NAME} \
		-p ${BACKEND_PORT}:${BACKEND_PORT} \
		--env DATABASE_HOST=${DATABASE_HOST} \
		--env DATABASE_PORT=${DATABASE_PORT} \
		--env DATABASE_NAME=${DATABASE_NAME} \
		--env DATABASE_USER=${DATABASE_USER} \
		--env DATABASE_PASSWORD=${DATABASE_PASSWORD} \
		${BACKEND_IMAGE_NAME}
backend-down:
	docker stop ${BACKEND_CONTAINER_NAME} && docker rm ${BACKEND_CONTAINER_NAME}