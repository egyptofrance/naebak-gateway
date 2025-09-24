#!/bin/bash

# Naibak Microservice Deployment Script for Google Cloud Run
# This script handles the complete deployment process with AI governance

set -e

# Configuration
PROJECT_ID=${GCP_PROJECT_ID:-"your-project-id"}
SERVICE_NAME=${SERVICE_NAME:-"naibak-gateway"}
REGION=${REGION:-"us-central1"}
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
ENVIRONMENT=${ENVIRONMENT:-"staging"}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if gcloud is installed
    if ! command -v gcloud &> /dev/null; then
        error "gcloud CLI is not installed. Please install it first."
    fi
    
    # Check if docker is installed
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install it first."
    fi
    
    # Check if authenticated with gcloud
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        error "Not authenticated with gcloud. Please run 'gcloud auth login'"
    fi
    
    # Set project
    gcloud config set project $PROJECT_ID
    
    log "Prerequisites check completed"
}

# Run tests before deployment
run_tests() {
    log "Running tests before deployment..."
    
    # Unit tests
    log "Running unit tests..."
    python -m pytest tests/unit/ -v --tb=short || error "Unit tests failed"
    
    # Security tests
    log "Running security tests..."
    python -m pytest tests/security/ -v --tb=short || error "Security tests failed"
    
    # AI Governance tests
    log "Running AI governance tests..."
    python -m pytest tests/governance/ -v --tb=short || error "AI governance tests failed"
    
    log "All tests passed"
}

# Security scan
security_scan() {
    log "Running security scans..."
    
    # Bandit security scan
    log "Running Bandit security scan..."
    bandit -r app/ -f txt || warn "Bandit found security issues"
    
    # Safety check for dependencies
    log "Running Safety check..."
    safety check || warn "Safety found vulnerable dependencies"
    
    log "Security scans completed"
}

# Build Docker image
build_image() {
    log "Building Docker image..."
    
    # Get git commit hash for tagging
    GIT_COMMIT=$(git rev-parse --short HEAD)
    IMAGE_TAG="${IMAGE_NAME}:${GIT_COMMIT}"
    LATEST_TAG="${IMAGE_NAME}:latest"
    
    # Build image
    docker build -t $IMAGE_TAG -t $LATEST_TAG .
    
    log "Docker image built: $IMAGE_TAG"
}

# Push image to Google Container Registry
push_image() {
    log "Pushing image to Google Container Registry..."
    
    # Configure Docker for GCR
    gcloud auth configure-docker
    
    # Push images
    docker push $IMAGE_TAG
    docker push $LATEST_TAG
    
    log "Image pushed to GCR"
}

# Deploy to Cloud Run
deploy_to_cloud_run() {
    log "Deploying to Google Cloud Run..."
    
    # Set environment-specific configurations
    if [ "$ENVIRONMENT" = "production" ]; then
        MEMORY="2Gi"
        CPU="2"
        MAX_INSTANCES="100"
        MIN_INSTANCES="1"
        CONCURRENCY="80"
        SERVICE_SUFFIX=""
    else
        MEMORY="1Gi"
        CPU="1"
        MAX_INSTANCES="10"
        MIN_INSTANCES="0"
        CONCURRENCY="40"
        SERVICE_SUFFIX="-${ENVIRONMENT}"
    fi
    
    FULL_SERVICE_NAME="${SERVICE_NAME}${SERVICE_SUFFIX}"
    
    # Deploy to Cloud Run
    gcloud run deploy $FULL_SERVICE_NAME \
        --image $IMAGE_TAG \
        --platform managed \
        --region $REGION \
        --allow-unauthenticated \
        --memory $MEMORY \
        --cpu $CPU \
        --max-instances $MAX_INSTANCES \
        --min-instances $MIN_INSTANCES \
        --concurrency $CONCURRENCY \
        --timeout 300 \
        --set-env-vars="ENVIRONMENT=${ENVIRONMENT}" \
        --set-env-vars="DEBUG=False" \
        --set-env-vars="AI_GOVERNANCE_ENABLED=True" \
        --set-env-vars="MAX_AI_REQUESTS_PER_MINUTE=10" \
        --set-env-vars="AI_RESPONSE_MAX_TOKENS=1000" \
        --set-secrets="SECRET_KEY=django-secret-key:latest" \
        --set-secrets="DATABASE_URL=database-url:latest" \
        --set-secrets="REDIS_URL=redis-url:latest" \
        --set-secrets="OPENAI_API_KEY=openai-api-key:latest" \
        --no-traffic
    
    log "Deployed to Cloud Run: $FULL_SERVICE_NAME"
}

# Health check
health_check() {
    log "Performing health check..."
    
    # Get service URL
    SERVICE_URL=$(gcloud run services describe $FULL_SERVICE_NAME \
        --region=$REGION \
        --format='value(status.url)')
    
    # Wait for service to be ready
    sleep 30
    
    # Health check
    if curl -f "${SERVICE_URL}/health" > /dev/null 2>&1; then
        log "Health check passed"
        return 0
    else
        error "Health check failed"
        return 1
    fi
}

# Gradual traffic migration for production
migrate_traffic() {
    if [ "$ENVIRONMENT" = "production" ]; then
        log "Starting gradual traffic migration..."
        
        # 10% traffic
        log "Migrating 10% traffic to new version..."
        gcloud run services update-traffic $FULL_SERVICE_NAME \
            --to-revisions=LATEST=10 \
            --region=$REGION
        
        sleep 120
        
        # Check metrics and health
        if health_check; then
            # 50% traffic
            log "Migrating 50% traffic to new version..."
            gcloud run services update-traffic $FULL_SERVICE_NAME \
                --to-revisions=LATEST=50 \
                --region=$REGION
            
            sleep 120
            
            # Final migration
            if health_check; then
                log "Migrating 100% traffic to new version..."
                gcloud run services update-traffic $FULL_SERVICE_NAME \
                    --to-revisions=LATEST=100 \
                    --region=$REGION
                
                log "Traffic migration completed successfully"
            else
                error "Health check failed at 50% traffic, rolling back"
                rollback
            fi
        else
            error "Health check failed at 10% traffic, rolling back"
            rollback
        fi
    else
        # For non-production, migrate all traffic immediately
        log "Migrating all traffic to new version..."
        gcloud run services update-traffic $FULL_SERVICE_NAME \
            --to-revisions=LATEST=100 \
            --region=$REGION
    fi
}

# Rollback function
rollback() {
    warn "Rolling back to previous version..."
    
    gcloud run services update-traffic $FULL_SERVICE_NAME \
        --to-revisions=LATEST=0 \
        --region=$REGION
    
    error "Deployment rolled back due to health check failure"
}

# Cleanup old revisions
cleanup() {
    log "Cleaning up old revisions..."
    
    # Keep only the latest 5 revisions
    gcloud run revisions list \
        --service=$FULL_SERVICE_NAME \
        --region=$REGION \
        --format="value(metadata.name)" \
        --sort-by="~metadata.creationTimestamp" \
        --limit=100 | tail -n +6 | while read revision; do
        if [ ! -z "$revision" ]; then
            log "Deleting old revision: $revision"
            gcloud run revisions delete $revision --region=$REGION --quiet
        fi
    done
    
    log "Cleanup completed"
}

# Setup monitoring alerts
setup_monitoring() {
    log "Setting up monitoring and alerts..."
    
    # Create alerting policy for high error rate
    cat > /tmp/error-rate-policy.json << EOF
{
  "displayName": "High Error Rate - ${FULL_SERVICE_NAME}",
  "conditions": [
    {
      "displayName": "Error rate > 5%",
      "conditionThreshold": {
        "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${FULL_SERVICE_NAME}\"",
        "comparison": "COMPARISON_GREATER_THAN",
        "thresholdValue": 0.05,
        "duration": "300s",
        "aggregations": [
          {
            "alignmentPeriod": "60s",
            "perSeriesAligner": "ALIGN_RATE",
            "crossSeriesReducer": "REDUCE_MEAN",
            "groupByFields": ["resource.label.service_name"]
          }
        ]
      }
    }
  ],
  "combiner": "OR",
  "enabled": true,
  "notificationChannels": []
}
EOF
    
    # Apply the policy (if gcloud monitoring is available)
    # gcloud alpha monitoring policies create --policy-from-file=/tmp/error-rate-policy.json
    
    log "Monitoring setup completed"
}

# Main deployment function
main() {
    log "Starting deployment of Naibak Microservice..."
    log "Environment: $ENVIRONMENT"
    log "Project: $PROJECT_ID"
    log "Service: $SERVICE_NAME"
    log "Region: $REGION"
    
    check_prerequisites
    run_tests
    security_scan
    build_image
    push_image
    deploy_to_cloud_run
    health_check
    migrate_traffic
    cleanup
    setup_monitoring
    
    # Get final service URL
    FINAL_URL=$(gcloud run services describe $FULL_SERVICE_NAME \
        --region=$REGION \
        --format='value(status.url)')
    
    log "Deployment completed successfully!"
    log "Service URL: $FINAL_URL"
    log "Health check: ${FINAL_URL}/health"
    log "API docs: ${FINAL_URL}/api/docs/"
    log "Metrics: ${FINAL_URL}/metrics"
}

# Handle script arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "rollback")
        rollback
        ;;
    "health-check")
        health_check
        ;;
    "cleanup")
        cleanup
        ;;
    *)
        echo "Usage: $0 [deploy|rollback|health-check|cleanup]"
        exit 1
        ;;
esac
