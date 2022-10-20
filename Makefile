export dev_docker_compose = docker-compose -f docker-compose.dev.yml --env-file .env.dev
dev-database-up:
	${dev_docker_compose} up -d
dev-database-down:
	${dev_docker_compose} down