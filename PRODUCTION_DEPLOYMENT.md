# Production Deployment Guide

## Database Strategy

### Managed PostgreSQL is Essential

In production, use a **managed PostgreSQL service** rather than containerized databases:

**Why:**
- Automatic backups and point-in-time recovery
- Automatic failover and High Availability
- Automatic scaling
- Security patches applied automatically
- Monitoring and alerting built-in
- No operational overhead

### Cloud Provider Comparison

| Feature | AWS RDS | Google Cloud SQL | Azure | DigitalOcean | Self-Hosted |
|---------|---------|-----------------|-------|--------------|-------------|
| Automatic Backups | ✅ | ✅ | ✅ | ✅ | ❌ |
| HA/Failover | ✅ | ✅ | ✅ | ✅ | Manual |
| Monitoring | ✅ | ✅ | ✅ | ✅ | Third-party |
| Scaling | ✅ | ✅ | ✅ | ✅ | Manual |
| Cost | $$ | $$ | $$ | $ | Varies |
| Best For | Enterprise | GCP Users | Azure Users | Startups | Control |

## Recommended Setup: AWS RDS

### 1. Create RDS Instance

```bash
# Via AWS Console or CLI
aws rds create-db-instance \
  --db-instance-identifier ghost-investor-ai \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 15.3 \
  --master-username admin \
  --master-user-password YOUR_SECURE_PASSWORD \
  --allocated-storage 20 \
  --backup-retention-period 30 \
  --multi-az \
  --storage-encrypted
```

### 2. Configure Security Group

- Allow inbound on port 5432 from your app server only
- Restrict access by IP/security group

### 3. Get Connection String

```env
# Production .env
DATABASE_URL=postgresql://admin:PASSWORD@ghost-investor-ai.abc123.us-east-1.rds.amazonaws.com:5432/ghost_investor_ai
```

### 4. Initialize Database

```bash
# Connect and run migrations
python cli.py db-init --environment production
```

## Alternative: DigitalOcean (Simpler)

### 1. Create Managed Database

```bash
# Via DigitalOcean Console
# Choose PostgreSQL 15
# Select appropriate tier (Basic $15-50/month is usually enough)
```

### 2. Get Connection Info

```env
DATABASE_URL=postgresql://doadmin:PASSWORD@do-user-db.ondigitalocean.com:25060/ghost_investor_ai?sslmode=require
```

### 3. Initialize Database

```bash
python cli.py db-init --environment production
```

## Production Environment Configuration

### Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:pass@host:5432/ghost_investor_ai
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40
DATABASE_POOL_RECYCLE=3600

# API Keys
APOLLO_API_KEY=xxx
CLEARBIT_API_KEY=xxx
PEOPLE_DATA_LABS_API_KEY=xxx

# Email Integration
GMAIL_CLIENT_ID=xxx
GMAIL_CLIENT_SECRET=xxx

# CRM Integration
GHOSTCRM_API_KEY=xxx
GHOSTCRM_BASE_URL=https://ghostcrm.example.com

# App Settings
ENVIRONMENT=production
DEBUG=False
LOG_LEVEL=WARNING  # Less verbose in production

# Security
SECRET_KEY=generate-a-long-random-string
ALLOWED_HOSTS=api.yourdomain.com,ghost-investor-ai.yourdomain.com
```

### Database Connection Pooling

The app is configured for production pooling:

- **Production**: 20 base connections + 40 overflow
- **Development**: 5 base connections + 10 overflow
- **Connection recycling**: Every 1 hour
- **Health checks**: Every connection before use

This prevents connection leaks and handles database restarts gracefully.

## Deployment Options

### Option 1: AWS ECS (Recommended)

Container-based deployment:
```bash
# Push Docker image to ECR
docker build -t ghost-investor-ai .
docker tag ghost-investor-ai:latest YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/ghost-investor-ai:latest
docker push ...

# Create ECS task definition pointing to RDS
# Set environment variables
# Scale as needed
```

### Option 2: Heroku (Simplest)

```bash
# Add Heroku Postgres
heroku addons:create heroku-postgresql:standard-0

# Deploy
git push heroku main

# migrations run automatically
```

### Option 3: Kubernetes (Enterprise)

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ghost-investor-ai
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: app
        image: ghost-investor-ai:latest
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: url
        - name: ENVIRONMENT
          value: "production"
```

## Backup Strategy

### Automated Backups (Managed Services)

All managed PostgreSQL services provide:
- **Daily automated backups**
- **Point-in-time recovery** (usually 30-35 days)
- **Automated failover** in case of failure

Check your provider's backup dashboard regularly.

### Manual Backups (Security Best Practice)

```bash
# Backup to local file
pg_dump -h your-db-host -U admin -d ghost_investor_ai > backup_$(date +%Y%m%d).sql

# Backup to S3
pg_dump postgresql://... | gzip | aws s3 cp - s3://your-bucket/backups/db_$(date +%Y%m%d).sql.gz

# Restore from backup
psql postgresql://... < backup_20260318.sql
```

### Set Up Automated Backups to S3

```bash
#!/bin/bash
# daily-backup.sh
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BUCKET="your-backup-bucket"
DB_URL="$DATABASE_URL"

pg_dump "$DB_URL" | gzip | \
aws s3 cp - s3://$BUCKET/ghost-investor-ai/db_$TIMESTAMP.sql.gz

# Keep only last 30 days
aws s3 rm s3://$BUCKET/ghost-investor-ai/ --recursive \
  --exclude "*" --include "db_*" \
  --older-than 30
```

## Monitoring & Alerts

### CloudWatch / Native Monitoring

Monitor these metrics:
- **CPU Usage**: Alert if > 80%
- **Database Connections**: Alert if > 90% of pool
- **Storage**: Alert if > 85% used
- **Read/Write Latency**: Alert if > 200ms
- **Failed Connections**: Alert if any

### Application Logging

Log to CloudWatch/Stackdriver:

```python
# Add to main.py for production
import logging
from watchtower import CloudWatchLogHandler

if settings.environment == "production":
    handler = CloudWatchLogHandler()
    logging.getLogger().addHandler(handler)
```

### Database Query Performance

```bash
# Monitor slow queries
# In PostgreSQL:
ALTER DATABASE ghost_investor_ai SET log_min_duration_statement = 1000;  # Log queries > 1s

# View logs
tail -f /var/log/postgresql/postgresql.log
```

## Scaling the Database

### Read Replicas (for read-heavy workloads)

If you have many enrichment queries:

```bash
# AWS RDS: Create read replica
aws rds create-db-instance-read-replica \
  --db-instance-identifier ghost-investor-ai-read-1 \
  --source-db-instance-identifier ghost-investor-ai
```

Update app to route read-only queries:
```python
# Advanced: Use separate read connection
READ_DATABASE_URL = "postgresql://user:pass@read-replica-host:5432/db"
```

### Vertical Scaling (Increase Instance Size)

If current instance is too small:
- AWS RDS: Change DB instance class (usually 5-15 min downtime)
- No code changes needed

### Database Optimization

```sql
-- Create indexes on frequently queried columns
CREATE INDEX idx_leads_email ON leads(email);
CREATE INDEX idx_leads_company ON leads(company_name);
CREATE INDEX idx_activities_lead_id ON activities(lead_id);
CREATE INDEX idx_outreach_emails_lead_id ON outreach_emails(lead_id);

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM leads WHERE company_name = 'xxx';
```

## Security Best Practices

1. **Enable SSL/TLS**
   ```python
   # Use SSL for database connections
   DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
   ```

2. **Restrict Network Access**
   - Use security groups / VPC
   - Allow only app servers to connect

3. **Use IAM Authentication** (AWS)
   ```bash
   # AWS RDS IAM auth (no password in code)
   aws rds describe-db-instances --query 'DBInstances[0].Endpoint'
   ```

4. **Encrypt Data at Rest**
   - Enable in managed service console
   - AWS RDS: Check "Enable encryption"

5. **Rotate Credentials Regularly**
   - Change master password every 90 days
   - Store in secret manager (AWS Secrets Manager, HashiCorp Vault)

## Cost Optimization

### AWS RDS Pricing Example

```
db.t3.micro:      ~$30/month + $0.23/GB storage
db.t3.small:      ~$60/month + $0.23/GB storage
db.t3.medium:     ~$120/month + $0.23/GB storage
```

**Estimation for your app:**
- Storage: ~10-20 GB (leads, emails, activities)
- Expected cost: **$40-60/month** for t3.micro

### Cost Reduction Tips

- Use **db.t3.micro** for most workloads
- Enable **storage autoscaling** instead of pre-allocating
- Use **DigitalOcean** for 30-40% cost savings
- Use **RDS Reserved Instances** for 30% discount on 1-3 year commitments

## Migration Path: Local → Production

1. **Develop locally with Docker**
   ```bash
   docker-compose up -d
   ```

2. **Test with managed DB in staging**
   ```env
   DATABASE_URL=postgresql://...managed-service...
   ENVIRONMENT=staging
   ```

3. **Deploy to production**
   ```env
   DATABASE_URL=postgresql://...production...
   ENVIRONMENT=production
   ```

4. **Point orchestrator to production URL**
   ```
   API: https://api.yourdomain.com
   Health: https://api.yourdomain.com/health
   ```

## Disaster Recovery Plan

### Recovery Time Objective (RTO): < 1 hour
### Recovery Point Objective (RPO): < 15 minutes

1. **Automated backups**: Daily + point-in-time
2. **Replicate to different region**: For critical systems
3. **Test restores**: Monthly disaster recovery drill
4. **Document runbook**: How to restore

### Quick Restore Procedure

```bash
# If database is corrupted
# 1. Create new RDS instance from latest snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier ghost-investor-ai-restored \
  --db-snapshot-identifier latest-snapshot

# 2. Update app DATABASE_URL to point to new instance
# 3. Test connectivity
# 4. Update DNS/load balancer if needed

# Total time: ~5-10 minutes
```

## Production Checklist

- ✅ Database: Managed PostgreSQL (RDS, Cloud SQL, Azure, or DigitalOcean)
- ✅ Backups: Automated daily + restore tested
- ✅ Monitoring: CloudWatch/native service monitoring configured
- ✅ Security: SSL/TLS enabled, network restricted, credentials in secrets manager
- ✅ Logging: Application logs sent to centralized logging service
- ✅ Health checks: Orchestrator can verify service health
- ✅ Scaling: Horizontal/vertical scaling plan documented
- ✅ DR Plan: Backup restore procedure tested
- ✅ Performance: Database optimized with indexes
- ✅ Cost: Budget set and alerts configured

## Summary

**Local Development**: Docker PostgreSQL  
**Production**: Managed PostgreSQL Service (AWS RDS, Google Cloud SQL, Azure, or DigitalOcean)

Estimated monthly cost: **$40-100** depending on scale and provider.

The Ghost Investor AI app is configured to work seamlessly with any PostgreSQL instance—just change the `DATABASE_URL`!
