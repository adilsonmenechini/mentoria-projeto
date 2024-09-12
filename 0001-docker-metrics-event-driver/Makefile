.PHONY: application prometheus grafana rabbit postgres nginx

# Application
application:
	@docker-compose --env-file .env -f application/docker-compose.yml up -d --build --force-recreate

prometheus:
	@docker-compose --env-file .env -f tools/prometheus/docker-compose.yaml up -d --build --force-recreate

grafana:
	@docker-compose --env-file .env -f tools/grafana/docker-compose.yaml up -d --build --force-recreate

rabbit:
	@docker-compose --env-file .env -f tools/rabbitmq/docker-compose.yaml up -d --build --force-recreate

postgres:
	@docker-compose --env-file .env -f tools/postgresql/docker-compose.yaml up -d --build --force-recreate

nginx:
	@docker-compose -f tools/nginx/docker-compose.yaml up -d --build --force-recreate

tools: rabbit prometheus grafana postgres nginx

clean:
	@docker rm -f $$(docker ps -a -q)
	@docker system prune -f
	@docker volume rm -f $$(docker volume ls -q)
	@docker rmi -f $$(docker images -q)