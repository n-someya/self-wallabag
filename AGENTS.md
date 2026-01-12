# Agent Rules

This repository contains specific rules for AI agents (Claude, Antigravity, etc.) to follow.

## Rules

### 1. Backup `terraform.tfvars` before modification
- **Rule**: Whenever you modify `backend/src/terraform/terraform.tfvars`, you must first create a backup.
- **Backup File Pattern**: `terraform.tfvars.bak`
- **Git Ignore**: The `.bak` extension is already included in `.gitignore` to prevent sensitive data from being committed. Ensure that the backup remains ignored.

### 2. Environment Alignment
- **Rule**: Configuration in `terraform.tfvars` should prioritize alignment with the root `.env` file where applicable.
