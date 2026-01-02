# Deployment Guide

## Prerequisites

Before deploying the IoT Smart City Platform, ensure you have:

- Docker 20.10+ and Docker Compose 2.0+
- At least 4GB RAM available
- 20GB free disk space
- Network access for pulling Docker images
- (Optional) Kubernetes cluster for production deployment

## Local Development Deployment

### 1. Clone the Repository

```bash
git clone https://github.com/romanchaa997/smart-bakhmach-iot-infrastructure.git
cd smart-bakhmach-iot-infrastructure
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration
nano .env
```

**Important:** Change the `JWT_SECRET_KEY` to a secure random string in production!

### 3. Start Services

```bash
docker-compose up -d
```

### 4. Verify Deployment

```bash
# Check all services are running
docker-compose ps

# Check logs
docker-compose logs -f

# Test API Gateway
curl http://localhost:8000/health
```

### 5. Initialize with Sample Data (Optional)

```bash
# Login to get token
TOKEN=$(curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" | jq -r '.access_token')

# Register a smart meter
curl -X POST "http://localhost:8001/api/v1/meters" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"meter_id":"METER001","location":"Main Street 123","meter_type":"three_phase"}'
```

## Production Deployment

### Docker Compose (Recommended for Single Server)

1. **Update docker-compose.yml for production:**

```yaml
# Update postgres section with volumes for persistence
volumes:
  - /var/lib/postgresql/data:/var/lib/postgresql/data

# Add restart policies
restart: always

# Configure resource limits
deploy:
  resources:
    limits:
      cpus: '0.5'
      memory: 512M
```

2. **Set up reverse proxy (Nginx):**

```nginx
server {
    listen 80;
    server_name iot.bakhmach.ua;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

3. **Enable SSL with Let's Encrypt:**

```bash
sudo certbot --nginx -d iot.bakhmach.ua
```

4. **Start services:**

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Kubernetes Deployment

1. **Convert Docker Compose to Kubernetes:**

```bash
kompose convert -f docker-compose.yml
```

2. **Create namespace:**

```bash
kubectl create namespace iot-platform
```

3. **Create secrets:**

```bash
kubectl create secret generic iot-secrets \
  --from-literal=jwt-secret-key='your-secret-key' \
  --from-literal=db-password='your-db-password' \
  -n iot-platform
```

4. **Deploy services:**

```bash
kubectl apply -f k8s/ -n iot-platform
```

5. **Expose services:**

```bash
kubectl expose deployment api-gateway --type=LoadBalancer --port=80 --target-port=8000 -n iot-platform
```

### AWS ECS/Fargate Deployment

1. **Push images to ECR:**

```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ECR_URL
docker-compose build
docker tag api-gateway:latest YOUR_ECR_URL/api-gateway:latest
docker push YOUR_ECR_URL/api-gateway:latest
# Repeat for all services
```

2. **Create ECS Task Definitions:**

Use the provided JSON templates in `deploy/ecs/` directory.

3. **Create ECS Services:**

```bash
aws ecs create-service --cluster iot-platform --service-name api-gateway --task-definition api-gateway:1 --desired-count 2
```

## Database Migration

### Initial Setup

The database schema is automatically initialized via `scripts/init-db.sql` when the PostgreSQL container starts for the first time.

### Manual Migration

If you need to run migrations manually:

```bash
# Connect to database
docker-compose exec postgres psql -U iotuser -d iot_platform

# Run SQL script
\i /docker-entrypoint-initdb.d/init-db.sql
```

## Backup and Recovery

### Database Backup

```bash
# Backup
docker-compose exec postgres pg_dump -U iotuser iot_platform > backup_$(date +%Y%m%d).sql

# Restore
docker-compose exec -T postgres psql -U iotuser iot_platform < backup_20240101.sql
```

### Volume Backup

```bash
# Backup all volumes
docker run --rm -v iot_postgres-data:/data -v $(pwd):/backup ubuntu tar czf /backup/postgres-backup.tar.gz -C /data .
```

## Monitoring and Logging

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api-gateway

# Last 100 lines
docker-compose logs --tail=100
```

### Prometheus Integration (Optional)

The services expose Prometheus metrics. To scrape:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'iot-platform'
    static_configs:
      - targets:
        - 'api-gateway:8000'
        - 'energy-service:8001'
        - 'water-service:8002'
        - 'transport-service:8003'
        - 'air-quality-service:8004'
        - 'ml-analytics-service:8005'
```

## Scaling

### Horizontal Scaling

```bash
# Scale energy service to 3 instances
docker-compose up -d --scale energy-service=3

# In Kubernetes
kubectl scale deployment energy-service --replicas=3 -n iot-platform
```

### Auto-scaling with Kubernetes

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: energy-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: energy-service
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## Health Checks

All services expose `/health` endpoints. Set up monitoring:

```bash
# Simple health check script
for port in 8000 8001 8002 8003 8004 8005; do
  curl -f http://localhost:$port/health || echo "Service on port $port is down"
done
```

## Troubleshooting

### Services won't start

```bash
# Check logs
docker-compose logs

# Verify ports are available
netstat -tuln | grep -E '8000|8001|8002|8003|8004|8005|5432|9092|1883'

# Remove and recreate
docker-compose down -v
docker-compose up -d
```

### Database connection issues

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Test connection
docker-compose exec postgres psql -U iotuser -d iot_platform -c "SELECT 1;"
```

### Kafka issues

```bash
# Check Kafka logs
docker-compose logs kafka

# Check Zookeeper
docker-compose logs zookeeper

# List topics
docker-compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list
```

## Security Checklist

- [ ] Change default JWT secret key
- [ ] Change default database password
- [ ] Enable SSL/TLS for all services
- [ ] Set up firewall rules
- [ ] Enable authentication for Kafka and MQTT
- [ ] Regular security updates
- [ ] Monitor for suspicious activity
- [ ] Implement rate limiting
- [ ] Set up intrusion detection
- [ ] Regular backups

## Performance Optimization

1. **Database Indexes:** Already configured in `init-db.sql`
2. **Connection Pooling:** Configure in production
3. **Caching:** Consider Redis for frequently accessed data
4. **CDN:** Use for static assets
5. **Load Balancing:** Use nginx or AWS ALB

## Updates and Maintenance

### Update Services

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d
```

### Zero-downtime Updates (Kubernetes)

```bash
kubectl set image deployment/energy-service energy-service=new-image:tag -n iot-platform
kubectl rollout status deployment/energy-service -n iot-platform
```

## Support

For deployment issues:
- GitHub Issues: https://github.com/romanchaa997/smart-bakhmach-iot-infrastructure/issues
- Email: admin@bakhmach.ua
- Documentation: https://github.com/romanchaa997/smart-bakhmach-iot-infrastructure/docs
