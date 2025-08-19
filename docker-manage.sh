#!/bin/bash

# Bangladesh News Scraper - Docker Management Script
echo "==============================================="
echo "Bangladesh News Scraper - Docker Management"
echo "==============================================="

function show_help() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start     - Start all services"
    echo "  stop      - Stop all services"
    echo "  restart   - Restart all services"
    echo "  status    - Show container status"
    echo "  logs      - Show application logs"
    echo "  build     - Build and start all services"
    echo "  clean     - Stop and remove all containers and volumes"
    echo "  health    - Check application health"
    echo "  help      - Show this help message"
    echo ""
    echo "Services:"
    echo "  Main API:              http://localhost:8000"
    echo "  API Documentation:     http://localhost:8000/docs"
    echo "  Flower (Celery UI):    http://localhost:5555"
    echo "  MongoDB:               localhost:27017"
    echo "  Redis:                 localhost:6379"
}

function start_services() {
    echo "Starting all services..."
    docker-compose up -d
    echo "Services started successfully!"
    echo "API: http://localhost:8000"
    echo "Docs: http://localhost:8000/docs"
    echo "Flower: http://localhost:5555"
}

function stop_services() {
    echo "Stopping all services..."
    docker-compose down
    echo "Services stopped successfully!"
}

function restart_services() {
    echo "Restarting all services..."
    docker-compose restart
    echo "Services restarted successfully!"
}

function show_status() {
    echo "Container status:"
    docker-compose ps
    echo ""
    echo "Service URLs:"
    echo "  Main API:              http://localhost:8000"
    echo "  API Documentation:     http://localhost:8000/docs"
    echo "  Flower (Celery UI):    http://localhost:5555"
}

function show_logs() {
    echo "Application logs (last 50 lines):"
    docker-compose logs --tail=50 app
}

function build_services() {
    echo "Building and starting all services..."
    docker-compose up --build -d
    echo "Services built and started successfully!"
    echo "API: http://localhost:8000"
    echo "Docs: http://localhost:8000/docs"
    echo "Flower: http://localhost:5555"
}

function clean_services() {
    echo "WARNING: This will remove all containers and data!"
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose down -v
        docker system prune -f
        echo "All containers and volumes removed!"
    else
        echo "Operation cancelled."
    fi
}

function check_health() {
    echo "Checking application health..."
    response=$(curl -s http://localhost:8000/health)
    if [ $? -eq 0 ]; then
        echo "✓ Application is healthy"
        echo "Response: $response"
    else
        echo "✗ Application is not responding"
        echo "Check container status with: $0 status"
    fi
}

# Main command handling
case "${1:-help}" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    build)
        build_services
        ;;
    clean)
        clean_services
        ;;
    health)
        check_health
        ;;
    help|*)
        show_help
        ;;
esac
