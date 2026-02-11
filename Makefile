# Variables
DOCKER_COMPOSE = docker compose
DOCKER = docker
PYTHON = python3
SRC_DIR = src

.PHONY: help up down restart build logs ps migrate revision lint format check clean

help:
	@echo "Available commands:"
	@echo "  up        - Start containers in background"
	@echo "  down      - Stop and remove containers"
	@echo "  restart   - Restart all containers"
	@echo "  start     - Start all containers"
	@echo "  stop      - Stop all containers"
	@echo "  build     - Build containers"
	@echo "  logs      - View container logs"
	@echo "  ps        - Show running containers"
	@echo "  bot       - Open bot container shell"
	@echo "  db        - Open db container shell"
	@echo "  redis-clear - Clear redis data"
	@echo "  prune     - Prune unused containers"

up:
	$(DOCKER_COMPOSE) up -d

down:
	$(DOCKER_COMPOSE) down

restart:
	$(DOCKER_COMPOSE) restart
start:
	$(DOCKER_COMPOSE) start

stop:
	$(DOCKER_COMPOSE) stop

build:
	$(DOCKER_COMPOSE) build

logs:
	$(DOCKER_COMPOSE) logs -f

logs-bot:
	$(DOCKER_COMPOSE) logs -f bot

ps:
	$(DOCKER_COMPOSE) ps

bot:
	${DOCKER_COMPOSE} exec bot bash

db:
	${DOCKER_COMPOSE} exec db bash

redis-clear:
	${DOCKER_COMPOSE} exec redis redis-cli flushall

prune:
	${DOCKER} image prune -f

