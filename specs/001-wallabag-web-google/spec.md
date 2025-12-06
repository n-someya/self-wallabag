# Feature Specification: Self-hosted Wallabag Web Clipping Service

**Feature Branch**: `001-wallabag-web-google`  
**Created**: 2025-09-25  
**Status**: Draft  
**Input**: User description: "wallabagを利用して、Web記事をクリッピングするサービスをセルフホストしたいと思っています
     。当面は自分自身しか利用者がいないと思われるので、Google Cloud Runを利用してホスティングを行いたいです。ただし認証を
     つけたいと思っており、APIKeyによる保護をしたいと考えています。まずは、Wallabag
     v2をAsIsでホスティングするところまで実施したいです。将来的にはクリップした記事を解析するサービスを別建てすることを考
     えています。そのため、DBはsupabaseのPostgreSQLを利用しようと考えてます"

## User Scenarios & Testing

### Primary User Story
As a sole user, I want to self-host a Wallabag service on Google Cloud Run to clip and save web articles for later reading, with API key protection to ensure only I can access the service.

### Acceptance Scenarios
1. **Given** Wallabag v2 is deployed on Google Cloud Run, **When** I access the service with a valid API key, **Then** I should be able to see the Wallabag interface.
2. **Given** I am authenticated to the Wallabag service, **When** I use a browser extension or bookmarklet to clip an article, **Then** the article should be saved to my Wallabag instance.
3. **Given** I have clipped articles in my Wallabag instance, **When** I access the service, **Then** I should be able to view and manage my saved articles.
4. **Given** I am using the Wallabag service, **When** I try to access it without a valid API key, **Then** access should be denied.
5. **Given** Wallabag is connected to Supabase PostgreSQL, **When** I save articles, **Then** the data should be persistently stored in the database.

### Edge Cases
- What happens when the API key is incorrectly provided or expired?
- How does the system handle failed article fetching due to network issues or blocked content?
- What happens when the database connection fails temporarily?
- How does the system handle articles with non-standard formatting or content types?
- What happens if the Cloud Run instance is restarted while processing a clip operation?

## Requirements

### Functional Requirements
- **FR-001**: System MUST deploy Wallabag v2 on Google Cloud Run.
- **FR-002**: System MUST use Supabase PostgreSQL for data storage.
- **FR-003**: System MUST implement API key authentication to restrict access.
- **FR-004**: System MUST allow clipping web articles using standard Wallabag methods (browser extensions, bookmarklet).
- **FR-005**: System MUST save all clipped articles to the PostgreSQL database.
- **FR-006**: System MUST provide standard Wallabag article management features (reading, tagging, organizing, searching).
- **FR-007**: System MUST maintain configurations and settings across Cloud Run instance restarts.
- **FR-008**: System MUST validate API keys before allowing access to any functionality.
- **FR-009**: System MUST support accessing the Wallabag service from various client devices (desktops, mobile phones, tablets).
- **FR-010**: System MUST allow future integration with a separate article analysis service [NEEDS CLARIFICATION: specific integration points or data sharing mechanisms].

### Key Entities
- **Clipped Article**: A saved web page or content, including original URL, title, content, timestamp, read/unread status, and any user-added tags or notes.
- **Authentication**: API key verification mechanism that restricts access to authorized users only.
- **User Configuration**: User preferences, display settings, and personalization options that persist across sessions.
- **Database Connection**: The link between the Wallabag service and the Supabase PostgreSQL database, including connection strings and access configurations.

## Review & Acceptance Checklist

### Content Quality
- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

### Requirement Completeness
- [ ] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous  
- [x] Success criteria are measurable
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Execution Status
- [x] User description parsed
- [x] Key concepts extracted
- [x] Ambiguities marked
- [x] User scenarios defined
- [x] Requirements generated
- [x] Entities identified
- [ ] Review checklist passed