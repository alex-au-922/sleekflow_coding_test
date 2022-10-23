export dev_docker_compose = docker-compose -f docker-compose.dev.yml --env-file .env.dev
dev-database-up:
	${dev_docker_compose} up -d
dev-database-down:
	${dev_docker_compose} down
generate-schema:
	cd backend && python create_schema.py
dev-backend-up:
	cd backend && python main.py