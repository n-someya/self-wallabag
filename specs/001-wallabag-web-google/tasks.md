# Tasks: Self-hosted Wallabag Web Clipping Service

**Input**: Design documents from `/specs/001-wallabag-web-google/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Phase 3.1: Setup

- [X] T001 Create project structure per implementation plan in backend/
- [X] T002 [P] Clone Wallabag GitHub repository with specific release tag (v2.5+) in backend/src/wallabag-source/
- [X] T003 [P] Initialize Docker environment with PHP 8.1+ in backend/src/docker/
- [X] T004 [P] Create Terraform module for Google Cloud Run in backend/src/terraform/cloud_run.tf
- [X] T005 [P] Create Terraform module for Supabase PostgreSQL in backend/src/terraform/supabase.tf
- [X] T006 [P] Configure project dependencies for Wallabag in backend/src/config/
- [X] T007 [P] Set up development environment with Docker Compose in backend/docker-compose.yml
- [X] T008 [P] Set up Python test environment for API tests in backend/tests/requirements.txt and backend/tests/conftest.py

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3

**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

- [X] T009 [P] Contract test GET /api/entries endpoint in backend/tests/contract/test_entries_get.py
- [X] T010 [P] Contract test POST /api/entries endpoint in backend/tests/contract/test_entries_post.py
- [X] T011 [P] Contract test PATCH /api/entries/{id} endpoint in backend/tests/contract/test_entries_patch.py
- [X] T012 [P] Contract test DELETE /api/entries/{id} endpoint in backend/tests/contract/test_entries_delete.py
- [X] T013 [P] Contract test GET /api-keys endpoint in backend/tests/contract/test_api_keys_get.py
- [X] T014 [P] Contract test POST /api-keys endpoint in backend/tests/contract/test_api_keys_post.py
- [X] T015 [P] Contract test DELETE /api-keys/{id} endpoint in backend/tests/contract/test_api_keys_delete.py
- [X] T016 [P] Integration test for Database connection in backend/tests/integration/test_database_connection.py
- [X] T017 [P] Integration test for article clipping scenario in backend/tests/integration/test_article_clipping.py
- [X] T018 [P] Integration test for article management scenario in backend/tests/integration/test_article_management.py
- [X] T019 [P] Integration test for failed authentication scenario in backend/tests/integration/test_failed_auth.py
- [X] T020 [P] Unit test for Article entity in backend/tests/unit/test_article_entity.php
- [X] T021 [P] Unit test for User entity in backend/tests/unit/test_user_entity.php
- [X] T022 [P] Unit test for API Key authentication in backend/tests/unit/test_api_key_auth.php

## Phase 3.3: Core Implementation (ONLY after tests are failing)

- [X] T023 [P] Implement Article entity configuration in backend/src/config/entity/article.php
- [X] T024 [P] Implement User entity configuration in backend/src/config/entity/user.php
- [X] T025 [P] Implement API Key entity configuration in backend/src/config/entity/api_key.php
- [X] T026 [P] Implement Tag entity configuration in backend/src/config/entity/tag.php
- [X] T027 [P] Create API key generation script in backend/src/auth/generate-api-key.sh
- [X] T028 [P] Configure Wallabag parameters.yml template in backend/src/config/parameters.yml.dist
- [X] T029 Create Dockerfile that copies local Wallabag source code and uses PHP 8.1+ in backend/src/docker/Dockerfile
- [X] T030 Create Docker build script that handles source code preparation in backend/src/docker/build.sh
- [X] T031 Create Cloud Run IAM configuration for API authentication in backend/src/terraform/iam.tf
- [X] T032 Configure Terraform variables and outputs in backend/src/terraform/variables.tf and outputs.tf
- [X] T033 Create Terraform main configuration in backend/src/terraform/main.tf
- [X] T034 Implement database migration scripts in backend/src/config/migrations/

## Phase 3.4: Integration

- [X] T035 Configure Supabase PostgreSQL connection in backend/src/config/db_connection.php
- [X] T036 Implement API key authentication middleware in backend/src/auth/api_key_middleware.php
- [X] T037 Create deployment script for Cloud Run in backend/src/deploy.sh
- [X] T038 Configure environment variables for production in backend/src/config/env.sh
- [X] T039 Implement logging configuration in backend/src/config/logging.php
- [X] T040 Set up HTTPS and security headers in backend/src/config/security.php

## Phase 3.5: Polish

- [X] T041 [P] Create performance test for article parsing in backend/tests/performance/test_article_parsing.py
- [X] T042 [P] Create performance test for API response time in backend/tests/performance/test_api_response.py
- [ ] T043 [P] Add monitoring configuration for Cloud Run in backend/src/terraform/monitoring.tf
- [ ] T044 [P] Create backup script for Supabase PostgreSQL in backend/src/backup/backup.sh
- [X] T045 [P] Create documentation for API usage in backend/docs/api.md
- [X] T046 [P] Create documentation for deployment in backend/docs/deployment.md
- [X] T047 [P] Create documentation for maintenance in backend/docs/maintenance.md
- [X] T048 Run complete system test following quickstart.md instructions

## Dependencies

- Setup tasks (T001-T008) must be completed first
- T002 (Clone Wallabag repository) must be done before T029 (Dockerfile creation)
- T008 (Python test environment) must be done before API tests (T009-T019)
- Tests (T009-T022) must be written before implementation (T023-T034)
- Core implementation tasks (T023-T034) before integration tasks (T035-T040)
- All implementation must be complete before polish tasks (T041-T048)
- T023-T026 (entity configurations) should be done before T035 (database connection)
- T027 (API key generation) must be done before T036 (API key middleware)
- T028 (parameters template) must be done before T029 (Dockerfile)
- T004, T005 (Terraform modules) must be done before T033 (main configuration)
- T029, T030 (Dockerfile and build script) must be coordinated to correctly handle local source code

## Parallel Execution Examples

```
# Launch all Python API contract tests together:
Task: "Contract test GET /api/entries endpoint in backend/tests/contract/test_entries_get.py"
Task: "Contract test POST /api/entries endpoint in backend/tests/contract/test_entries_post.py"
Task: "Contract test PATCH /api/entries/{id} endpoint in backend/tests/contract/test_entries_patch.py"
Task: "Contract test DELETE /api/entries/{id} endpoint in backend/tests/contract/test_entries_delete.py"
Task: "Contract test GET /api-keys endpoint in backend/tests/contract/test_api_keys_get.py"
Task: "Contract test POST /api-keys endpoint in backend/tests/contract/test_api_keys_post.py"
Task: "Contract test DELETE /api-keys/{id} endpoint in backend/tests/contract/test_api_keys_delete.py"

# Launch all PHP unit tests together:
Task: "Unit test for Article entity in backend/tests/unit/test_article_entity.php"
Task: "Unit test for User entity in backend/tests/unit/test_user_entity.php"
Task: "Unit test for API Key authentication in backend/tests/unit/test_api_key_auth.php"

# Launch all entity configurations together:
Task: "Implement Article entity configuration in backend/src/config/entity/article.php"
Task: "Implement User entity configuration in backend/src/config/entity/user.php"
Task: "Implement API Key entity configuration in backend/src/config/entity/api_key.php"
Task: "Implement Tag entity configuration in backend/src/config/entity/tag.php"

# Launch all documentation tasks together:
Task: "Create documentation for API usage in backend/docs/api.md"
Task: "Create documentation for deployment in backend/docs/deployment.md"
Task: "Create documentation for maintenance in backend/docs/maintenance.md"
```

## Notes

- [P] tasks can be executed in parallel as they work on different files
- All tests must fail initially to follow TDD principles
- API tests are written in Python to test the API remotely
- Unit tests are written in PHP to match the implementation language
- Terraform code must follow Infrastructure as Code best practices
- Docker configuration should allow for local testing before cloud deployment
- API key authentication is implemented at both Cloud Run (IAM) and application levels
- Wallabag source code is cloned from GitHub with specific release tag and copied into the Docker image during build