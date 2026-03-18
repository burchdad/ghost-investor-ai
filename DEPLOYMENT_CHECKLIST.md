"""DEPLOYMENT CHECKLIST

Ghost Investor AI Phase 1 - Production Deployment Guide

## Pre-Deployment Requirements

### Infrastructure Setup ✅ Complete
- [ ] PostgreSQL database provisioned (AWS RDS, etc.)
- [ ] Redis cluster provisioned (AWS ElastiCache, etc.)
- [ ] Application server(s) allocated
- [ ] Celery worker server(s) allocated
- [ ] SSL/TLS certificates obtained

### Third-Party Services ✅ Complete
- [ ] Gmail OAuth app created (https://console.cloud.google.com)
  - Client ID obtained
  - Client Secret obtained
  - Redirect URIs configured
  - Test users added

- [ ] Outlook OAuth app created (https://portal.azure.com)
  - Application ID obtained
  - Client Secret obtained
  - Redirect URIs configured

- [ ] OpenAI API key obtained
  - Account created and verified
  - API key generated
  - Usage limits set

- [ ] GhostCRM integration configured (if applicable)
  - API key obtained
  - Base URL confirmed
  - Webhook endpoint configured

### Security Setup ✅ Complete
- [ ] JWT secret key generated (strong, 256+ bit)
- [ ] Database password randomized
- [ ] OAuth credentials encrypted in transit
- [ ] API rate limits configured
- [ ] CORS origins configured (not *)
- [ ] HTTPS enforced
- [ ] Security headers configured

---

## Deployment Steps

### 1. Database Migration
```bash
# Connect to production database
export DATABASE_URL=postgresql://user:pass@prod-db.region.rds.amazonaws.com/ghost_investor_ai

# Run migrations
alembic upgrade head

# Verify tables created
psql $DATABASE_URL -c "\\dt"
```

### 2. Environment Configuration
```bash
# Create production .env
# Must include:
- DATABASE_URL (production)
- CELERY_BROKER_URL (Redis prod)
- CELERY_RESULT_BACKEND_URL (Redis prod)
- OPENAI_API_KEY
- GMAIL_CLIENT_ID & GMAIL_CLIENT_SECRET
- OUTLOOK_CLIENT_ID & OUTLOOK_CLIENT_SECRET
- GHOSTCRM_API_KEY & GHOSTCRM_BASE_URL
- JWT_SECRET_KEY (strong random)
- ENVIRONMENT=production
- DEBUG=False
- LOG_LEVEL=INFO
```

### 3. Deploy Application Server
```bash
# Build Docker image
docker build -t ghost-investor-ai:v1.0.0 .

# Push to registry (ECR, DockerHub, etc.)
docker tag ghost-investor-ai:v1.0.0 your-registry/ghost-investor-ai:v1.0.0
docker push your-registry/ghost-investor-ai:v1.0.0

# Deploy via Kubernetes, ECS, App Engine, etc.
# Ensure: PYTHONPATH=./src is set
# Health check: GET /health should return {"status":"ok"}
```

### 4. Deploy Celery Worker(s)
```bash
# Deploy Celery worker service
# Command: celery -A src.ghost_investor_ai.services.batch_jobs worker --loglevel=info

# Configure auto-restart
# Use systemd, supervisor, or container orchestration

# Monitor worker logs
tail -f celery-worker.log
```

### 5. Health Checks
```bash
# API health
curl https://api.example.com/health

# Database connectivity
psql -d ghost_investor_ai -c "SELECT 1"

# Redis connectivity
redis-cli -h prod-redis.example.com PING

# Celery worker status
celery -A src.ghost_investor_ai.services.batch_jobs inspect active
```

### 6. Monitoring Setup
```bash
# Configure logging (CloudWatch, Stackdriver, etc.)
# - API errors and warnings
# - Celery task execution times
# - Database query performance
# - Redis memory usage

# Configure alerts for:
- Task queue depth > 1000
- Worker offline
- Database connection errors
- Redis memory > 80%
- API error rate > 1%
- Email send failures
```

### 7. SSL/TLS Configuration
```bash
# Obtain SSL certificate (Let's Encrypt, AWS Certificate Manager, etc.)
# Configure in load balancer/reverse proxy
# Force HTTPS redirect

# Verify:
curl --insecure https://api.example.com/health | grep status
```

---

## Testing Before Go-Live

### Unit Tests
```bash
pytest tests.py -v --cov=src/ghost_investor_ai
```

### Integration Tests
```bash
# Test email authorization flow (Gmail)
# Test batch enrichment with test leads
# Test email generation with OpenAI
# Test email sending with test recipients
# Test reply classification
# Test GhostCRM sync
```

### Load Testing
```bash
# Test with Apache Bench or wrk
wrk -t12 -c400 -d30s https://api.example.com/health

# Test batch job submission (Celery)
# Simulate 100 concurrent campaigns
# Monitor worker queue depth and processing time
```

### Canary Deployment
```bash
# Deploy to 10% of traffic
# Monitor error rates
# Monitor latency
# If stable, increase to 50%
# If still stable, rollout 100%
```

---

## Post-Deployment Checklist

### Monitoring
- [ ] Application logs flowing to central logger
- [ ] Error alerts configured and tested
- [ ] Performance metrics being collected
- [ ] Celery task metrics visible
- [ ] Database metrics monitored
- [ ] Redis memory/performance monitored

### Backups
- [ ] Database backups scheduled (daily minimum)
- [ ] Backup retention policy set (30 days minimum)
- [ ] Backup restoration tested
- [ ] Point-in-time recovery verified

### Security
- [ ] Secrets rotated (JWT key, DB password)
- [ ] Security headers configured
- [ ] CORS origins restricted
- [ ] Rate limiting verified working
- [ ] OAuth tokens secured
- [ ] API audit logging enabled

### Documentation
- [ ] Deployment runbook created
- [ ] Rollback procedure documented
- [ ] Team trained on system
- [ ] On-call rotation established
- [ ] Incident response process defined

### Performance
- [ ] API response times < 200ms (p95)
- [ ] Email send latency < 100ms
- [ ] Batch jobs processing efficiently
- [ ] Database queries optimized
- [ ] Connection pooling verified

### Operations
- [ ] Monitoring dashboard created
- [ ] Alert channels configured (Slack, PagerDuty, etc.)
- [ ] Weekly health checks scheduled
- [ ] Monthly security review scheduled
- [ ] Cost tracking enabled

---

## Production Configuration Recommendations

### Database (PostgreSQL)
```
Instance Type: db.t3.medium minimum (Production)
Storage: 100GB+ with auto-scaling
Backup: 35-day retention
Multi-AZ: Enabled
VPC: Private subnet
Connection Pooling: 20 connections, 40 max
Query Log: Enable slow query log (> 1s)
```

### Cache (Redis)
```
Instance Type: cache.t3.micro minimum
Memory: 1GB minimum (scales with usage)
Multi-AZ: Enabled for high availability
Eviction Policy: volatile-lru
Persistence: RDB snapshots enabled (daily)
```

### Application
```
Container: 0.5-1 CPU, 1-2GB RAM per instance
Auto-scaling: Min 2, Max 10 based on CPU
Load balancer: Application ELB with health checks
Deployment: Blue-green or canary
Rollback: Immediate (n-1 stable version)
```

### Celery Workers
```
Workers: Minimum 2 (for redundancy)
Concurrency: 4 tasks per worker
Timeout: 1 hour soft limit
Memory limit: 1GB per task
Monitoring: Task execution time, queue depth
```

---

## Rollback Procedures

### Quick Rollback (If Critical Issue)
```bash
# 1. Route traffic to previous version
docker service scale api=0
docker service update --image ghost-investor-ai:v0.9.0 api
docker service scale api=3

# 2. Monitor error rates
# 3. If stable, restart workers
# 4. Run database health check
```

### Database Rollback
```bash
# If migration causes issue:
alembic downgrade -1
# Or specific version:
alembic downgrade 123456
```

### Cache Rollback
```bash
# Flush and restart if corrupted
redis-cli FLUSHALL
redis-cli restart
```

---

## Success Criteria for Production

✅ All health checks passing
✅ No errors in application logs (first 24 hours)
✅ Email authorization flow working
✅ Batch jobs processing successfully
✅ Email generation working (using real OpenAI API)
✅ Reply parsing running
✅ GhostCRM sync operational
✅ Performance SLAs met
✅ Monitoring and alerting active
✅ Team trained and prepared
✅ Incident response tested

---

## Go-Live Checklist

- [ ] All infrastructure provisioned
- [ ] All secrets configured
- [ ] Database migrations complete
- [ ] SSL/TLS certificate installed
- [ ] Load balancer configured
- [ ] DNS updated (carefully)
- [ ] Monitoring enabled
- [ ] Backups verified
- [ ] Rollback plan documented
- [ ] Team on-call and ready
- [ ] Communication plan executed
- [ ] Status page updated

---

## Post-Launch (Week 1)

Day 1-2:
- [ ] Monitor error rates (should be < 0.1%)
- [ ] Monitor performance (p95 latency < 200ms)
- [ ] Check email delivery rates
- [ ] Verify batch job queue depth

Day 3-5:
- [ ] Run load test if quiet period
- [ ] Review and optimize slow queries
- [ ] Collect early user feedback
- [ ] Gather performance metrics

Week 1 Review:
- [ ] Incident retrospective (if any)
- [ ] Performance analysis
- [ ] Cost analysis
- [ ] Update runbooks based on experience

---

## Ongoing Maintenance

### Daily
- [ ] Monitor logs for errors
- [ ] Check worker health
- [ ] Verify backups ran

### Weekly
- [ ] Review performance metrics
- [ ] Check database size trends
- [ ] Test failover/recovery

### Monthly
- [ ] Security audit
- [ ] Database optimization
- [ ] Cost analysis
- [ ] Team review + lessons learned

---

## Contact & Support

For deployment questions or issues:
1. Check PHASE1_STARTUP.md for local troubleshooting
2. Review logs in central logging system
3. Check ARCHITECTURE.md for system design questions
4. Escalate critical issues to on-call team

---

**Deployment Target: Week of [DATE]**
**Expected downtime: 0 minutes (blue-green deployment)**
**Estimated data migration time: < 5 minutes**

Good luck! 🚀
"""