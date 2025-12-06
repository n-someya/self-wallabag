<!-- 
# Sync Impact Report
- Version change: 1.0.0 → 1.1.0 (Minor version increase due to expanded guidance on external database usage)
- List of modified principles:
  - Modified: III. Infrastructure as Code (expanded to include external resource management)
- Added sections:
  - Added guidance for external database usage under "Technology Stack and Standards"
- Templates requiring updates: 
  - ✅ updated: .specify/templates/plan-template.md (added external database connection check)
  - ⚠ pending: .specify/templates/spec-template.md (add database connection section)
  - ⚠ pending: .specify/templates/tasks-template.md (add external database connection tasks)
- Follow-up TODOs:
  - Complete updates to spec and tasks templates to include external database connection considerations
-->

# Self-Wallabag Project Constitution

## Core Principles

### I. Test-Driven Development

All application code MUST be developed using test-driven development (TDD) methodology. Tests MUST be written before implementing the corresponding functionality. This approach ensures that requirements are clearly understood before implementation and that all code is testable by design.

### II. Test Strategy and Quality

Application testing MUST include appropriate combinations of black-box and white-box testing approaches. Black-box testing MUST focus on behavior and functionality from the user's perspective. White-box testing MUST verify internal logic and edge cases. Test coverage MUST be comprehensive, with a focus on behavior rather than implementation details.

### III. Infrastructure as Code

All infrastructure MUST be defined and managed using Infrastructure as Code (IaC) principles. Environment configurations MUST be version-controlled, reproducible, and automated. Manual infrastructure changes are PROHIBITED except in emergency situations, and must be followed by updates to the IaC definitions. When using existing external resources (such as databases), connection configurations MUST still be managed via IaC with appropriate abstraction for connection parameters.

### IV. Full-Stack Development Approach

The project encompasses frontend applications, backend services, and infrastructure components. All components MUST adhere to consistent quality standards across the stack. Each layer MUST have appropriate testing strategies, with automated tests validating the interactions between components.

### V. Continuous Integration and Delivery

All code changes MUST pass through automated CI/CD pipelines that enforce quality gates including test coverage, code style, and security checks. Integration tests MUST verify compatibility across components before deployment. Failed tests or quality checks MUST block merging and deployment.

## Technology Stack and Standards

The project supports a full technology stack including frontend, backend, and infrastructure components. Specific technologies must be documented and standardized across the project. All components must follow established best practices for their respective technologies. Deviations from standard patterns require explicit justification and approval.

When utilizing external databases or services:
- Connection strings and credentials MUST be passed via environment variables, never hardcoded
- Configuration MUST be parameterized to accept connection details at deployment time
- Connection validation MUST be implemented with proper error handling
- Deployment scripts MUST support both new resource provisioning and existing resource connection

## Development Workflow

Development follows a feature branch workflow with peer review requirements. New features or changes must be developed in isolated branches and submitted for review before integration. Code reviews must verify adherence to the core principles, particularly test coverage and quality. Changes to infrastructure require additional review by team members with infrastructure expertise.

## Governance

This constitution supersedes all other project practices and standards. Any amendments to this constitution require documentation, approval by project leadership, and a clear migration plan for existing code. Version control follows semantic versioning principles, with major version changes for backward-incompatible modifications, minor version changes for new principles or expanded guidance, and patch changes for clarifications.

All pull requests and code reviews MUST verify compliance with these principles. Implementation complexity must be justified when it impacts maintainability or testability. Development teams MUST consult this constitution when planning and implementing features.

**Version**: 1.1.0 | **Ratified**: 2025-09-25 | **Last Amended**: 2025-10-09