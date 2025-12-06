# Wallabag Maintenance Guide

This document provides comprehensive instructions for maintaining a Wallabag instance deployed on Google Cloud Run with Supabase PostgreSQL.

## Table of Contents

1. [Routine Maintenance](#routine-maintenance)
2. [Updating Wallabag](#updating-wallabag)
3. [Database Maintenance](#database-maintenance)
4. [Monitoring and Logging](#monitoring-and-logging)
5. [Backups and Recovery](#backups-and-recovery)
6. [Troubleshooting](#troubleshooting)
7. [Security Maintenance](#security-maintenance)
8. [Performance Optimization](#performance-optimization)
9. [Maintenance Checklist](#maintenance-checklist)

## Routine Maintenance

### Weekly Tasks

1. **Check for Errors**
   ```bash
   # View Cloud Run service logs
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=wallabag AND severity>=ERROR" --limit=50
   ```

2. **Monitor Resource Usage**
   ```bash
   # Check Cloud Run metrics
   gcloud monitoring metrics list | grep run.googleapis.com
   ```

3. **Check Database Health**
   - Log into Supabase dashboard
   - Review database metrics and connection statistics
   - Check for slow queries and optimize if necessary

### Monthly Tasks

1. **Update Security Patches**
   - Review Docker base image for security updates
   - Update dependencies and rebuild container if needed

2. **Clean Up Old Data**
   ```bash
   # Run cleanup task through Cloud Scheduler
   gcloud scheduler jobs run wallabag-cleanup
   ```

3. **Check API Key Usage**
   - Review API key usage and revoke unused keys
   - Check for suspicious access patterns

## Updating Wallabag

### Minor Version Updates

1. **Update Source Code**
   ```bash
   cd backend/src/wallabag-source
   git fetch
   git checkout [new_version_tag]
   cd ../..
   ```

2. **Rebuild Container**
   ```bash
   ./docker/build.sh --clean --image wallabag:new-version
   docker tag wallabag:new-version gcr.io/[PROJECT_ID]/wallabag:new-version
   docker push gcr.io/[PROJECT_ID]/wallabag:new-version
   ```

3. **Update Cloud Run Service**
   ```bash
   # Using the deploy script
   ./deploy.sh deploy --image gcr.io/[PROJECT_ID]/wallabag:new-version
   
   # Or manually
   gcloud run services update wallabag --image gcr.io/[PROJECT_ID]/wallabag:new-version
   ```

4. **Run Database Migrations**
   ```bash
   # Using Cloud Run job
   gcloud run jobs create wallabag-migrations \
     --image gcr.io/[PROJECT_ID]/wallabag:new-version \
     --command="/bin/bash" \
     --args="-c,cd /var/www/html && bin/console doctrine:migrations:migrate --no-interaction --env=prod" \
     --memory=512Mi
   
   gcloud run jobs execute wallabag-migrations
   ```

### Major Version Updates

For major version updates, additional steps may be required:

1. **Backup Database First**
   ```bash
   # Run backup
   gcloud scheduler jobs run wallabag-backup-db --location us-central1
   ```

2. **Review Release Notes**
   - Check for breaking changes
   - Update config files as needed

3. **Test in Staging Environment**
   - Deploy to a separate Cloud Run service for testing
   - Verify all functionality works as expected
   - Test database migrations

4. **Plan Maintenance Window**
   - Schedule update during low-usage period
   - Notify users of maintenance if applicable

5. **Perform Update**
   - Follow minor update steps
   - Allow extra time for database migrations
   - Monitor logs closely during update

## Database Maintenance

### Database Optimization

1. **Run VACUUM Analysis**
   ```bash
   # Connect to database
   psql "postgresql://[USER]:[PASSWORD]@[HOST]:[PORT]/wallabag"
   
   # Run vacuum analyze
   VACUUM ANALYZE;
   ```

2. **Check for Index Bloat**
   ```sql
   SELECT
     schemaname, tablename, indexname,
     pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
     pg_size_pretty(pg_relation_size(indrelid)) as table_size
   FROM pg_stat_all_indexes
   ORDER BY pg_relation_size(indexrelid) DESC
   LIMIT 10;
   ```

3. **Optimize Slow Queries**
   - Review slow query log in Supabase dashboard
   - Add indexes for frequently queried columns
   - Consider materialized views for complex reports

### Database Schema Updates

When schema changes are needed:

1. **Create Migration File**
   ```bash
   # Create a new migration in backend/src/config/migrations/
   cp Version20251004000002.php Version$(date +%Y%m%d%H%M%S).php
   ```

2. **Edit Migration File**
   - Implement `up()` method for forward migration
   - Implement `down()` method for rollback
   - Test migration locally

3. **Deploy Migration**
   - Add migration file to Docker image
   - Run migration script after deployment

## Monitoring and Logging

### Setting Up Alerts

1. **CPU and Memory Usage**
   ```bash
   # Create alert for high CPU usage
   gcloud alpha monitoring policies create \
     --display-name="Wallabag High CPU" \
     --condition-filter="resource.type = 'cloud_run_revision' AND resource.labels.service_name = 'wallabag' AND metric.type = 'run.googleapis.com/container/cpu/utilization' AND metric.labels.state = 'used' AND metric.value > 0.8"
   ```

2. **Error Rate Alerts**
   ```bash
   # Create alert for high error rate
   gcloud alpha monitoring policies create \
     --display-name="Wallabag Error Rate" \
     --condition-filter="resource.type = 'cloud_run_revision' AND resource.labels.service_name = 'wallabag' AND metric.type = 'run.googleapis.com/request_count' AND metric.labels.response_code_class = '5xx' AND metric.value > 10"
   ```

### Log Analysis

Regular log analysis tasks:

1. **Check for Authentication Failures**
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=wallabag AND textPayload:('Authentication failure' OR 'Invalid API key')" --limit=20
   ```

2. **Monitor Slow Database Queries**
   ```bash
   # Filter logs for slow queries
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=wallabag AND textPayload:('Query took')" --limit=20
   ```

3. **Track API Usage**
   ```bash
   # Count API requests by endpoint
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=wallabag AND textPayload:('/api/')" --format="table(textPayload)" | grep -o "/api/[^ ]* " | sort | uniq -c | sort -nr
   ```

## Backups and Recovery

### Database Backups

Configure automated backups:

1. **Schedule Regular Backups**
   ```bash
   # Create Cloud Scheduler job for backups
   gcloud scheduler jobs create http wallabag-backup-db \
     --schedule="0 2 * * *" \
     --uri="https://YOUR_SERVICE_URL/backup" \
     --http-method=POST \
     --headers="Authorization=Bearer YOUR_BACKUP_TOKEN"
   ```

2. **Export Database on Demand**
   ```bash
   # Manual database export
   export DB_USER="your_db_user"
   export DB_PASS="your_db_password"
   export DB_HOST="your_supabase_host"
   export DB_PORT="5432"
   export DB_NAME="wallabag"
   export BACKUP_FILE="wallabag_$(date +%Y%m%d_%H%M%S).sql"
   
   # Run pg_dump
   pg_dump --host=$DB_HOST --port=$DB_PORT --username=$DB_USER --dbname=$DB_NAME > $BACKUP_FILE
   
   # Upload to Google Cloud Storage
   gsutil cp $BACKUP_FILE gs://your-backup-bucket/wallabag/
   ```

### Recovery Procedure

In case of data loss or corruption:

1. **Stop the Service**
   ```bash
   # Route traffic to previous revision
   gcloud run services update-traffic wallabag --to-revisions=wallabag-00001-abcd=100
   ```

2. **Restore Database**
   ```bash
   # Download backup
   gsutil cp gs://your-backup-bucket/wallabag/backup_file.sql .
   
   # Restore database
   psql --host=$DB_HOST --port=$DB_PORT --username=$DB_USER --dbname=$DB_NAME < backup_file.sql
   ```

3. **Verify Data Integrity**
   - Check if all entries and tags are restored
   - Verify user accounts and permissions
   - Test API functionality

4. **Resume Service**
   ```bash
   # Route traffic back to current revision
   gcloud run services update-traffic wallabag --to-latest
   ```

## Troubleshooting

### Common Issues

#### Database Connection Issues

**Symptoms:** 
- Application logs show "could not connect to server"
- HTTP 500 errors when accessing the service

**Resolution:**
1. Check Supabase status and dashboard
2. Verify connection parameters in environment variables
3. Test connection manually:
   ```bash
   psql "postgresql://[USER]:[PASSWORD]@[HOST]:[PORT]/[DBNAME]"
   ```
4. Check for IP restrictions in Supabase console

#### Memory/CPU Usage Issues

**Symptoms:**
- Application logs show out-of-memory errors
- Slow response times

**Resolution:**
1. Increase Cloud Run memory/CPU limits:
   ```bash
   gcloud run services update wallabag --memory 1Gi --cpu 2
   ```
2. Optimize database queries
3. Check for memory leaks in application code

#### API Authentication Problems

**Symptoms:**
- 401 Unauthorized errors
- API key rejection logs

**Resolution:**
1. Verify API key expiration dates
2. Check IAM permissions for Cloud Run service
3. Generate new API key if needed:
   ```bash
   ./backend/src/auth/generate-api-key.sh --user admin --name "New Key"
   ```

## Security Maintenance

### Regular Security Tasks

1. **Audit API Key Usage**
   ```sql
   -- Query database for API key usage
   SELECT api_key.id, api_key.name, api_key.created_at, api_key.last_used_at, users.username
   FROM wallabag_api_key api_key
   JOIN wallabag_user users ON users.id = api_key.user_id
   ORDER BY api_key.last_used_at DESC;
   ```

2. **Update SSL Certificates**
   - If using custom domain, ensure SSL certificates are renewed
   - Cloud Run handles this automatically for *.run.app domains

3. **Check for Vulnerabilities**
   ```bash
   # Scan Docker image for vulnerabilities
   trivy image gcr.io/[PROJECT_ID]/wallabag:latest
   ```

4. **Review IAM Permissions**
   ```bash
   # List IAM permissions for service
   gcloud projects get-iam-policy [PROJECT_ID] --format=json | jq '.bindings[] | select(.members[] | contains("serviceAccount:wallabag"))'
   ```

### Security Incident Response

In case of a security incident:

1. **Isolate the Service**
   ```bash
   # Restrict access to service
   gcloud run services update wallabag --no-allow-unauthenticated
   ```

2. **Rotate Credentials**
   - Generate new API keys
   - Update database passwords
   - Rotate service account keys

3. **Audit Access Logs**
   ```bash
   # Check recent access
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=wallabag" --limit=1000
   ```

## Performance Optimization

### Performance Testing

1. **Run Performance Tests**
   ```bash
   # Test article parsing performance
   cd backend/tests/performance
   python test_article_parsing.py --base-url https://your-service-url
   
   # Test API response time
   python test_api_response.py --base-url https://your-service-url
   ```

2. **Load Testing**
   - Use tools like Apache JMeter or k6 for load testing
   - Target common API endpoints
   - Gradually increase load to find breaking points

3. **Database Query Optimization**
   ```sql
   -- Identify slow queries
   SELECT query, calls, total_time, mean_time
   FROM pg_stat_statements
   ORDER BY total_time DESC
   LIMIT 10;
   ```

### Scaling Recommendations

1. **Vertical Scaling**
   - Increase CPU/memory for Cloud Run instances
   - Update database plan in Supabase if needed

2. **Horizontal Scaling**
   - Adjust minimum/maximum instances:
   ```bash
   gcloud run services update wallabag --min-instances=2 --max-instances=10
   ```

3. **Content Delivery**
   - Consider adding a CDN for static content
   - Configure caching headers appropriately

## Maintenance Checklist

### Weekly Checklist

- [ ] Review error logs for critical issues
- [ ] Check Cloud Run resource usage metrics
- [ ] Verify database backup jobs are running
- [ ] Run performance tests to monitor trends

### Monthly Checklist

- [ ] Apply security updates
- [ ] Review API key usage and remove unused keys
- [ ] Clean up old database records
- [ ] Check database performance metrics
- [ ] Optimize slow queries if identified
- [ ] Review IAM permissions

### Quarterly Checklist

- [ ] Update Wallabag version if new releases available
- [ ] Perform full backup testing with restore procedure
- [ ] Review and update monitoring thresholds
- [ ] Conduct security audit
- [ ] Update documentation if procedures changed

---

This maintenance guide should be reviewed and updated regularly to reflect any changes to the infrastructure or maintenance procedures.

*Last updated: October 2025*