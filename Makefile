.PHONY: dev stop build migrate logs test clean

# Start everything
dev:
	docker compose up --build -d
	@echo "✓ API:      http://localhost:8000/docs"
	@echo "✓ Frontend: http://localhost:3000"

# Stop everything
stop:
	docker compose down

# Rebuild containers
build:
	docker compose build --no-cache

# Run database migrations
migrate:
	docker compose exec backend alembic upgrade head

# Create a new migration
migration:
	docker compose exec backend alembic revision --autogenerate -m "$(msg)"

# View logs
logs:
	docker compose logs -f

logs-api:
	docker compose logs -f backend

# Run tests
test:
	docker compose exec backend pytest -v

# Reset database
reset-db:
	docker compose down -v
	docker compose up -d db
	sleep 3
	docker compose exec backend alembic upgrade head

# Clean everything
clean:
	docker compose down -v --rmi local
	rm -rf frontend/node_modules frontend/.next

# Import a CSV file
import:
	@echo "Usage: make import file=path/to/transactions.csv bank=monzo|starling"
	curl -X POST "http://localhost:8000/api/v1/transactions/upload" \
		-H "X-API-Key: $$(grep API_KEY .env | cut -d= -f2)" \
		-F "file=@$(file)" \
		-F "bank=$(bank)"
