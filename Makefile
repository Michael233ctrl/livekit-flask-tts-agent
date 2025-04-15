PROJECT_NAME=livekit_voice_pipeline
ENV_FILE=.env.local
COMPOSE=docker-compose --env-file $(ENV_FILE)

.PHONY: up down build restart logs prune clean ps shell


up:
	$(COMPOSE) up -d

stop:
	$(COMPOSE) stop

# Stop containers and remove network
down:
	$(COMPOSE) down

# Rebuild all images
build:
	$(COMPOSE) build --no-cache

# Restart all services
restart: down up

# Show running containers
ps:
	$(COMPOSE) ps

# View logs from all services
logs:
	$(COMPOSE) logs -f --tail=100

# Prune unused Docker objects (careful!)
prune:
	docker system prune -f --volumes

# Clean all: stop, remove containers, volumes, networks, images
clean:
	$(COMPOSE) down -v --rmi all --remove-orphans

# View environment variables from the .env file
env:
	@echo "Using environment file: $(ENV_FILE)"
	@cat $(ENV_FILE)

show:
	$(COMPOSE) ps