# Self-Hosted Wallabag on Google Cloud Run

A complete setup for deploying [Wallabag](https://wallabag.org) to Google Cloud Run with Supabase PostgreSQL database.

## Features

- 🚀 Deploy to Google Cloud Run with Terraform
- 🐘 Supabase PostgreSQL database integration
- 🔒 Secure credential management with Google Secret Manager
- 🐳 Docker Compose for local development and testing
- 📊 Cloud Monitoring and logging enabled
- 🔐 SSL/TLS encrypted database connections

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) (gcloud CLI)
- [Terraform](https://www.terraform.io/downloads) (>= 1.0.0)
- A [Supabase](https://supabase.com) account with a PostgreSQL database
- A Google Cloud Platform account

## Quick Start

### 1. Clone and Setup Environment

```bash
# Clone the repository
git clone <your-repo-url>
cd self-wallabag

# Run the setup script to create your .env file
./setup-env.sh
```

The setup script will prompt you for:
- GCP Project ID
- Supabase database credentials
- Other configuration options

### 2. Local Development with Supabase

Test your setup locally before deploying to Cloud Run:

```bash
# Start Wallabag connected to Supabase
docker-compose -f docker-compose.supabase.yml up

# In another terminal, initialize the database (first time only)
docker-compose -f docker-compose.supabase.yml exec wallabag \
  bin/console wallabag:install --env=prod --no-interaction
```

Access Wallabag at http://localhost:8080
- Default username: `wallabag`
- Default password: `wallabag`

### 3. Deploy to Google Cloud Run

#### a. Authenticate with GCP

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud auth configure-docker us-central1-docker.pkg.dev
```

#### b. Push Docker Image to Artifact Registry

```bash
# Tag the official Wallabag image
docker tag wallabag/wallabag:latest \
  us-central1-docker.pkg.dev/YOUR_PROJECT_ID/wallabag/wallabag:latest

# Push to Artifact Registry
docker push us-central1-docker.pkg.dev/YOUR_PROJECT_ID/wallabag/wallabag:latest
```

#### c. Configure Terraform Variables

```bash
cd backend/src/terraform

# Copy the template and edit with your values
cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars  # or use your preferred editor
```

Update the following values in `terraform.tfvars`:
- `project_id`: Your GCP project ID
- `supabase_project_ref`: Your Supabase project reference
- `supabase_host`: Your Supabase PostgreSQL pooler host
- `supabase_db_password`: Your Supabase database password
- `container_image`: Your Artifact Registry image path
- `env_vars["SYMFONY__ENV__DATABASE_USER"]`: Format `postgres.{your-project-ref}`
- `env_vars["POSTGRES_USER"]`: Same as above

#### d. Deploy with Terraform

```bash
# Initialize Terraform
terraform init

# Preview changes
terraform plan

# Deploy to Cloud Run
terraform apply -auto-approve
```

#### e. Initialize Database (First Deployment Only)

After the first deployment, initialize the database:

```bash
# Get the Cloud Run service URL
SERVICE_URL=$(terraform output -raw wallabag_url)

# The container will auto-initialize on first run
# Check logs to confirm
gcloud run services logs read wallabag \
  --region=us-central1 --limit=50
```

### 4. Access Your Wallabag Instance

```bash
# Get your service URL
terraform output wallabag_url

# Visit the URL in your browser
# Default credentials: wallabag / wallabag
# ⚠️ Change the password after first login!
```

## Project Structure

```
.
├── .env.example                    # Environment variables template
├── setup-env.sh                    # Interactive setup script
├── docker-compose.supabase.yml     # Docker Compose for Supabase connection
├── backend/src/terraform/          # Terraform infrastructure code
│   ├── main.tf                     # Main Terraform configuration
│   ├── cloud_run.tf                # Cloud Run service definition
│   ├── iam.tf                      # IAM roles and permissions
│   ├── variables.tf                # Variable definitions
│   ├── outputs.tf                  # Output values
│   ├── terraform.tfvars.example    # Terraform variables template
│   └── terraform.tfvars            # Your actual values (git-ignored)
└── report.md                       # Detailed setup documentation
```

## Configuration

### Environment Variables

Key environment variables (defined in `.env` for local, `terraform.tfvars` for Cloud Run):

| Variable | Description | Example |
|----------|-------------|---------|
| `SUPABASE_HOST` | Supabase PostgreSQL pooler host | `aws-0-ap-northeast-1.pooler.supabase.com` |
| `SUPABASE_DB_USER` | Full PostgreSQL username | `postgres.your-project-ref` |
| `SUPABASE_DB_PASSWORD` | Database password | `your-secure-password` |
| `SUPABASE_DB_NAME` | Database name | `wallabag_db` |
| `CLOUD_RUN_URL` | Your Cloud Run service URL | `https://wallabag-xxx-uc.a.run.app` |
| `WALLABAG_SECRET` | Application secret key (32+ chars) | Auto-generated by setup script |

### Security

- Database passwords are stored in Google Secret Manager
- SSL/TLS is required for all database connections (`sslmode=require`)
- Default credentials should be changed immediately after deployment
- Enable 2-factor authentication through Wallabag settings

## Management

### User Management

```bash
# Create a new user
docker-compose exec wallabag bin/console fos:user:create

# List all users
docker-compose exec wallabag bin/console wallabag:user:list

# Promote user to admin
docker-compose exec wallabag bin/console fos:user:promote username ROLE_SUPER_ADMIN

# Change password
docker-compose exec wallabag bin/console fos:user:change-password username newpassword
```

For Cloud Run:
```bash
# Run commands in Cloud Run (requires enabling Cloud Run admin access)
gcloud run services proxy wallabag --region=us-central1
```

### Database Backup

Your Supabase database has automatic backups. To create a manual backup:

1. Go to your Supabase dashboard
2. Navigate to Database → Backups
3. Click "Create backup"

### Monitoring

View logs and metrics:

```bash
# View recent logs
gcloud run services logs read wallabag --region=us-central1 --limit=100

# View service details
gcloud run services describe wallabag --region=us-central1

# View metrics in Cloud Console
gcloud console services describe wallabag
```

## Troubleshooting

### CSS Not Loading

If CSS assets are not loading properly, ensure `SYMFONY__ENV__DOMAIN_NAME` is set correctly:

```hcl
# In terraform.tfvars, main.tf sets this automatically
SYMFONY__ENV__DOMAIN_NAME = "https://your-actual-cloud-run-url.app"
```

### Database Connection Errors

1. Verify Supabase host is the pooler host (not direct connection host)
2. Check SSL mode is set to `require`
3. Confirm database `wallabag_db` exists
4. Verify credentials in Secret Manager

```bash
# Test database connection
psql "postgresql://postgres.PROJECT_REF:PASSWORD@POOLER_HOST:5432/postgres?sslmode=require"
```

### Migration Errors

If you see migration errors about unknown types:

```bash
# Manually run the Wallabag installer
docker-compose exec wallabag bin/console wallabag:install --env=prod
```

## Updating

### Update Wallabag Version

```bash
# Pull latest image
docker pull wallabag/wallabag:latest

# Re-tag and push to Artifact Registry
docker tag wallabag/wallabag:latest \
  us-central1-docker.pkg.dev/YOUR_PROJECT_ID/wallabag/wallabag:latest
docker push us-central1-docker.pkg.dev/YOUR_PROJECT_ID/wallabag/wallabag:latest

# Deploy with Terraform
cd backend/src/terraform
terraform apply -auto-approve
```

### Update Configuration

```bash
# Edit terraform.tfvars
nano backend/src/terraform/terraform.tfvars

# Apply changes
terraform plan
terraform apply
```

## Cost Estimation

Approximate monthly costs (as of 2024):

- **Cloud Run**: ~$5-20/month (depending on usage)
  - 512MB memory, 1 CPU
  - Pay per request
  - Free tier: 2 million requests/month

- **Supabase**: Free tier or $25/month (Pro plan)
  - Free: 500MB database, 2GB bandwidth
  - Pro: 8GB database, 50GB bandwidth

- **Secret Manager**: <$1/month
  - $0.06 per secret per month
  - $0.03 per 10,000 access operations

## Security Considerations

⚠️ **Important**:

1. Never commit `.env` or `terraform.tfvars` files
2. Rotate database passwords regularly
3. Enable 2FA for admin accounts
4. Review Cloud Run IAM policies
5. Use custom domain with Cloud Armor for DDoS protection
6. Monitor Cloud Logging for suspicious activity

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is provided as-is for self-hosting Wallabag. Wallabag itself is licensed under MIT.

## Support

- [Wallabag Documentation](https://doc.wallabag.org)
- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Terraform Documentation](https://www.terraform.io/docs)
- [Supabase Documentation](https://supabase.com/docs)

For issues specific to this setup, please open an issue in this repository.

## Acknowledgments

- [Wallabag Team](https://github.com/wallabag/wallabag) for the excellent read-it-later application
- Google Cloud Platform for Cloud Run
- Supabase for managed PostgreSQL

---

**Note**: This is a self-hosted solution. You are responsible for managing your own infrastructure, backups, and security.
