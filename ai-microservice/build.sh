#!/bin/bash
# Guardy AI Microservice - Build and Deploy Script
# Usage: ./build.sh [production|development]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="guardy-ai"
VERSION="1.0.0"
REGISTRY=""  # Set your Docker registry here, e.g., "docker.io/username"

# Functions
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    print_info "Checking requirements..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed"
        exit 1
    fi
    
    print_info "✅ Requirements satisfied"
}

build_production() {
    print_info "Building production image..."
    
    docker build \
        --target production \
        --tag ${IMAGE_NAME}:${VERSION} \
        --tag ${IMAGE_NAME}:latest \
        --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
        --build-arg VCS_REF=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown") \
        --build-arg VERSION=${VERSION} \
        .
    
    print_info "✅ Production image built: ${IMAGE_NAME}:${VERSION}"
}

build_development() {
    print_info "Building development image..."
    
    docker build \
        --target development \
        --tag ${IMAGE_NAME}:dev \
        .
    
    print_info "✅ Development image built: ${IMAGE_NAME}:dev"
}

push_image() {
    if [ -z "$REGISTRY" ]; then
        print_warning "No registry configured, skipping push"
        return
    fi
    
    print_info "Pushing image to registry..."
    
    docker tag ${IMAGE_NAME}:${VERSION} ${REGISTRY}/${IMAGE_NAME}:${VERSION}
    docker tag ${IMAGE_NAME}:latest ${REGISTRY}/${IMAGE_NAME}:latest
    
    docker push ${REGISTRY}/${IMAGE_NAME}:${VERSION}
    docker push ${REGISTRY}/${IMAGE_NAME}:latest
    
    print_info "✅ Image pushed to registry"
}

deploy_production() {
    print_info "Deploying production stack..."
    
    if [ ! -f .env ]; then
        print_error ".env file not found"
        print_info "Creating .env from .env.example..."
        cp .env.example .env
        print_warning "Please update .env with production values before deploying"
        exit 1
    fi
    
    docker-compose pull
    docker-compose up -d
    
    print_info "Waiting for services to be healthy..."
    sleep 10
    
    docker-compose ps
    
    print_info "✅ Production deployment complete"
    print_info "API: http://localhost:8000"
    print_info "Docs: http://localhost:8000/docs"
}

deploy_development() {
    print_info "Deploying development stack..."
    
    if [ ! -f .env ]; then
        print_info "Creating .env from .env.example..."
        cp .env.example .env
    fi
    
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
    
    print_info "Waiting for services to be healthy..."
    sleep 10
    
    docker-compose ps
    
    print_info "✅ Development deployment complete"
    print_info "API: http://localhost:8000"
    print_info "Docs: http://localhost:8000/docs"
    print_info "pgAdmin: http://localhost:5050"
    print_info "Redis Commander: http://localhost:8081"
}

stop_services() {
    print_info "Stopping services..."
    docker-compose down
    print_info "✅ Services stopped"
}

clean() {
    print_info "Cleaning up..."
    docker-compose down -v
    docker rmi ${IMAGE_NAME}:latest ${IMAGE_NAME}:${VERSION} ${IMAGE_NAME}:dev 2>/dev/null || true
    print_info "✅ Cleanup complete"
}

# Main script
main() {
    MODE=${1:-production}
    
    print_info "Guardy AI Microservice - Build & Deploy"
    print_info "Mode: $MODE"
    echo ""
    
    check_requirements
    
    case $MODE in
        production)
            build_production
            read -p "Push to registry? (y/N) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                push_image
            fi
            read -p "Deploy now? (y/N) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                deploy_production
            fi
            ;;
        development|dev)
            build_development
            read -p "Deploy now? (y/N) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                deploy_development
            fi
            ;;
        stop)
            stop_services
            ;;
        clean)
            clean
            ;;
        *)
            print_error "Unknown mode: $MODE"
            echo "Usage: $0 [production|development|stop|clean]"
            exit 1
            ;;
    esac
    
    echo ""
    print_info "Done! 🎉"
}

# Run main function
main "$@"
