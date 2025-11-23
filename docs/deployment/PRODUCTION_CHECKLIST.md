# Production Deployment Checklist
## Flask Schedule Webapp - Pre-Launch Verification

Use this checklist to ensure all production requirements are met before deployment.

---

## 🔒 Security Configuration

### Environment & Secrets
- [ ] **SECRET_KEY** generated with cryptographically secure random value (64+ characters)
- [ ] **.env file** permissions set to 600 (read/write owner only)
- [ ] **All credentials** stored in environment variables (not hardcoded)
- [ ] **WALMART_EDR_USERNAME** configured
- [ ] **WALMART_EDR_PASSWORD** configured
- [ ] **WALMART_EDR_MFA_CREDENTIAL_ID** configured
- [ ] **Database credentials** are secure and unique
- [ ] **.env** file added to .gitignore (never committed to git)

### Application Security
- [ ] **FLASK_ENV** set to `production`
- [ ] **DEBUG** mode disabled (False)
- [ ] **SESSION_COOKIE_SECURE** enabled (True for HTTPS)
- [ ] **SESSION_COOKIE_HTTPONLY** enabled (True)
- [ ] **CSRF protection** enabled
- [ ] **Security headers** configured in Nginx/reverse proxy
- [ ] **Rate limiting** enabled and configured
- [ ] **SQL injection** protection verified (using ORM)
- [ ] **XSS protection** verified (template escaping enabled)

### Network Security
- [ ] **SSL/TLS certificate** installed and valid
- [ ] **HTTPS** enforced (HTTP redirects to HTTPS)
- [ ] **Firewall** configured (only necessary ports open)
- [ ] **Database** not exposed to public internet
- [ ] **Admin interfaces** protected/disabled in production

---

## 🗄️ Database Configuration

### Database Setup
- [ ] **Production database** created (PostgreSQL recommended)
- [ ] **Database user** created with appropriate permissions
- [ ] **Database migrations** run (`flask db upgrade`)
- [ ] **Database connection pool** configured
- [ ] **Foreign key constraints** enabled
- [ ] **Database backups** configured and tested
- [ ] **Backup retention policy** defined

### Data Validation
- [ ] **Test data** verified or removed
- [ ] **Initial data** loaded if required
- [ ] **Database indexes** created for performance
- [ ] **Connection limits** configured appropriately

---

## 🚀 Application Deployment

### Code & Dependencies
- [ ] **Latest stable code** deployed from main/production branch
- [ ] **Python version** 3.11+ installed
- [ ] **Virtual environment** created and activated
- [ ] **All dependencies** installed from requirements.txt
- [ ] **Static files** collected/compiled if needed
- [ ] **File permissions** set correctly (scheduler user owns files)

### WSGI Server
- [ ] **Gunicorn** installed and configured
- [ ] **Worker count** optimized for server resources
- [ ] **Worker class** set (gevent for async)
- [ ] **Timeout settings** configured
- [ ] **Graceful reload** tested

### System Service
- [ ] **Systemd service** file created and enabled
- [ ] **Service starts** on system boot
- [ ] **Service restarts** on failure
- [ ] **Service user** created (non-root)
- [ ] **Working directory** configured correctly

---

## 🌐 Reverse Proxy & Web Server

### Nginx Configuration
- [ ] **Nginx** installed and running
- [ ] **Server block** configured for application
- [ ] **Proxy settings** configured correctly
- [ ] **Static files** served directly by Nginx
- [ ] **Upload size limits** configured
- [ ] **Timeout values** set appropriately
- [ ] **Compression** enabled (gzip)
- [ ] **HTTP/2** enabled

### SSL/TLS
- [ ] **SSL certificate** installed
- [ ] **Certificate auto-renewal** configured (Let's Encrypt)
- [ ] **TLS 1.2+** only (TLS 1.0/1.1 disabled)
- [ ] **Strong cipher suites** configured
- [ ] **HSTS header** configured

---

## 📊 Monitoring & Logging

### Health Checks
- [ ] **Health endpoints** accessible
  - [ ] /health/ping
  - [ ] /health/live
  - [ ] /health/ready
  - [ ] /health/status
  - [ ] /health/metrics
- [ ] **Uptime monitoring** configured (external service)
- [ ] **Alert notifications** set up

### Logging
- [ ] **Application logging** configured
- [ ] **Log level** set appropriately (WARNING/ERROR for production)
- [ ] **Log rotation** configured
- [ ] **Centralized logging** set up (optional but recommended)
- [ ] **Sensitive data** not logged (passwords, tokens, etc.)

### Metrics & Analytics
- [ ] **Prometheus metrics** endpoint accessible
- [ ] **Grafana dashboards** created (optional)
- [ ] **Error tracking** service integrated (Sentry, etc.) (optional)

---

## 💾 Backup & Recovery

### Backup Strategy
- [ ] **Database backup** automated (daily minimum)
- [ ] **Application files** backup configured
- [ ] **Backup retention** policy defined (7-30 days recommended)
- [ ] **Backup location** secure and separate from production
- [ ] **Backup restoration** tested successfully

### Disaster Recovery
- [ ] **Recovery procedure** documented
- [ ] **Recovery time objective (RTO)** defined
- [ ] **Recovery point objective (RPO)** defined
- [ ] **Backup verification** automated

---

## ⚡ Performance Optimization

### Application Performance
- [ ] **Database queries** optimized
- [ ] **Indexes** created on frequently queried columns
- [ ] **Caching** configured (Redis) if applicable
- [ ] **Static file caching** enabled (CDN or Nginx)
- [ ] **Connection pooling** configured
- [ ] **Session storage** optimized

### Resource Limits
- [ ] **Memory limits** set for application
- [ ] **CPU limits** set if using containerization
- [ ] **File descriptor limits** increased if needed
- [ ] **Request timeouts** configured

---

## 🧪 Testing & Validation

### Pre-Deployment Testing
- [ ] **Smoke tests** pass
- [ ] **Integration tests** pass
- [ ] **Load testing** performed
- [ ] **Security scanning** completed
- [ ] **Dependency vulnerabilities** checked
- [ ] **Manual testing** on staging environment

### Post-Deployment Validation
- [ ] **Application starts** successfully
- [ ] **Health checks** return 200 OK
- [ ] **Authentication** works
- [ ] **Database connectivity** verified
- [ ] **External API integration** working
- [ ] **Critical workflows** tested
- [ ] **Error pages** display correctly

---

## 📝 Documentation

### Required Documentation
- [ ] **Deployment guide** available (DEPLOYMENT.md)
- [ ] **README** updated with production information
- [ ] **API documentation** current
- [ ] **Configuration guide** available
- [ ] **Troubleshooting guide** available
- [ ] **Runbook** for common operations

### Team Communication
- [ ] **Deployment schedule** communicated
- [ ] **On-call rotation** established
- [ ] **Escalation path** documented
- [ ] **Access credentials** shared securely

---

## 🔄 Maintenance & Operations

### Regular Maintenance
- [ ] **Update schedule** defined
- [ ] **Maintenance windows** scheduled
- [ ] **Change management process** defined
- [ ] **Rollback procedure** documented and tested

### Monitoring Schedule
- [ ] **Daily health checks**
- [ ] **Weekly backup verification**
- [ ] **Monthly security updates**
- [ ] **Quarterly disaster recovery drills**

---

## ✅ Final Verification

### Go-Live Checklist
- [ ] All above items completed
- [ ] **Staging environment** matches production
- [ ] **DNS records** configured and propagated
- [ ] **Email notifications** working
- [ ] **SSL certificate** valid for at least 30 days
- [ ] **Backups running** and verified
- [ ] **Monitoring alerts** working
- [ ] **Team trained** on production operations
- [ ] **Support contacts** available
- [ ] **Go-live approval** obtained

### Post-Launch (First 24 Hours)
- [ ] **Monitor logs** for errors
- [ ] **Check health endpoints** regularly
- [ ] **Verify backups** completed successfully
- [ ] **Monitor resource usage** (CPU, memory, disk)
- [ ] **Test critical paths** with real users
- [ ] **Document any issues** encountered

---

## 🆘 Emergency Contacts

```
Primary On-Call: _____________________
Secondary On-Call: _____________________
Database Admin: _____________________
Infrastructure Team: _____________________
```

---

## Notes

Use this section to track deployment-specific notes, issues, or deviations from the standard checklist:

```
Date: ___________
Environment: ___________
Deployed By: ___________

Notes:




```

---

**Deployment Approved By:** _____________________ **Date:** ___________
