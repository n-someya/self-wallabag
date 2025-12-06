# Implementation Plan: Self-hosted Wallabag Web Clipping Service

**Branch**: `001-wallabag-web-google` | **Date**: 2025-10-09 | **Spec**: [spec.md](/specs/001-wallabag-web-google/spec.md)
**Input**: Feature specification from `/specs/001-wallabag-web-google/spec.md`

## Summary

Deploy Wallabag v2 on Google Cloud Run, using the existing Supabase PostgreSQL database as the data store. The deployment will include API key authentication for secure access. This implementation focuses on accepting the existing PostgreSQL connection string as an input parameter rather than provisioning a new database.

## Technical Context
**Language/Version**: PHP 8.1+  
**Primary Dependencies**: Docker, Terraform, Google Cloud Run, Supabase PostgreSQL  
**Storage**: Existing Supabase PostgreSQL  
**Testing**: Integration testing with API endpoints  
**Target Platform**: Google Cloud Run, Web browsers  
**Project Type**: Web (backend focus)  
**Performance Goals**: <1s response time for API calls, <3s for article parsing  
**Constraints**: Must use existing Supabase PostgreSQL instance with provided connection string  
**Scale/Scope**: Single-user deployment

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1. **Test-Driven Development**: Integration tests for API endpoints and database access will be created before implementing functionality.
2. **Test Strategy and Quality**: A combination of black-box testing (API endpoint behavior) and white-box testing (database connection configuration) will be employed.
3. **Infrastructure as Code**: All GCP and service configurations will be defined in Terraform.
4. **Full-Stack Development Approach**: The project focuses on backend configuration, with appropriate testing of web interfaces.
5. **Continuous Integration and Delivery**: CI/CD pipelines will be created for deployment with quality gates.

## Project Structure

### Documentation (this feature)
```
specs/001-wallabag-web-google/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
# Option 2: Web application
backend/
├── src/
│   ├── terraform/        # Infrastructure as Code definitions
│   ├── docker/           # Docker configuration for Wallabag
│   ├── scripts/          # Deployment and configuration scripts
│   └── config/           # Configuration templates
└── tests/
    ├── integration/      # Integration tests for API and database
    └── unit/             # Unit tests for configuration logic
```

**Structure Decision**: Option 2 (Web application) - Due to the nature of hosting a web service with database backend

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - Wallabag integration with existing PostgreSQL database
   - API key authentication implementation in Google Cloud Run
   - Optimal Docker configuration for Wallabag on Cloud Run
   - Database connection approach for existing Supabase instance

2. **Generate and dispatch research agents**:
   - Research Wallabag v2 system requirements and performance
   - Research API key authentication options for Wallabag
   - Research deploying PHP applications on Google Cloud Run
   - Research connecting Wallabag to existing PostgreSQL databases
   - Research Terraform configuration for Google Cloud Run
   - Research securing Wallabag with API keys
   - Research future integration for article analysis

3. **Consolidate findings** in `research.md` with decisions, rationales, and alternatives considered.

**Output**: [research.md](/specs/001-wallabag-web-google/research.md) with all research findings

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Article entity (core Wallabag content)
   - User entity (authentication)
   - API Key entity (access control)
   - Tag entity (organization)
   - Database Connection entity (configuration)
   - Cloud Run Configuration entity (deployment)

2. **Generate API contracts** from functional requirements:
   - Authentication API contract (OAuth/API Key)
   - Article API contract (CRUD operations)
   - Infrastructure configuration contract (Terraform)

3. **Generate contract tests** from contracts:
   - Test for API key authentication
   - Test for article saving and retrieval
   - Test for database connectivity with existing Supabase

4. **Extract test scenarios** from user stories:
   - Successful Wallabag deployment with API key access
   - Article clipping with browser extension
   - Article management (read, tag, organize)
   - Access restriction with invalid API key

5. **Update agent file incrementally** (O(1) operation):
   - Run `.specify/scripts/bash/update-agent-context.sh claude`
   - Add new tech context for Wallabag, Google Cloud Run, Supabase
   - Preserve project-specific details
   - Document recent changes for database connection configuration

**Output**: [data-model.md](/specs/001-wallabag-web-google/data-model.md), [contracts/*](/specs/001-wallabag-web-google/contracts/), [quickstart.md](/specs/001-wallabag-web-google/quickstart.md)

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Generate tasks from Phase 1 design docs (contracts, data model, quickstart)
- Each contract → contract test task [P]
- Infrastructure setup tasks (Terraform configuration)
- Docker configuration tasks (Wallabag container)
- Database connection configuration tasks (using existing Supabase)
- API key authentication tasks
- Deployment and testing tasks

**Ordering Strategy**:
- TDD order: Tests before implementation 
- Dependency order: Infrastructure before application before UI
- Mark [P] for parallel execution (independent files)

**Estimated Output**: 20-25 numbered, ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

No violations identified - the implementation follows all constitutional principles.

## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented

---
*Based on Constitution v1.0.0 - See `/memory/constitution.md`*