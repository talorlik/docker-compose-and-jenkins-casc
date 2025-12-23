# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### [Added]
- Added `setup-jenkins.sh` automation script for streamlined Jenkins setup
- Added Docker Cloud configuration for dynamic agent provisioning
- Added Docker Compose secrets support for secure password management
- Added `CHANGELOG.md` to track project changes
- Added `secrets/` directory for storing password files (git-ignored)
- Added `.env` file support for non-secret configuration variables

### [Changed]
- Changed user from "user" to "devops" for better clarity
- Updated password environment variable from `JENKINS_USER_PASSWORD` to `JENKINS_DEVOPS_PASSWORD`
- Migrated from hardcoded password defaults to secrets-based approach
- Updated `docker-compose.yaml` to use Docker Compose secrets
- Updated `jenkins.yaml` to include Docker Cloud configuration
- Updated location configuration to use environment variables (`JENKINS_URL`, `JENKINS_ADMIN_EMAIL`)
- Updated authorization strategy from `permissions` list to `entries` structure with user/group objects
- Updated Docker Cloud configuration structure:
  - Changed `dockerHost` to `dockerApi.dockerHost` with `connectTimeout` and `readTimeout`
  - Changed `instanceCap` to `instanceCapStr` (string format)
  - Changed `image` to `dockerTemplateBase.image`
  - Changed `pullStrategy` from `PULL_ALWAYS` to `PULL_LATEST`
  - Added `pullTimeout`, `connector.attach.user`, and `retentionStrategy.idleMinutes`
  - Updated agent image to `jenkins/inbound-agent:lts-jdk21`
- Updated crumb issuer configuration with explicit settings
- Updated all documentation to use `docker compose` syntax (replacing `docker-compose`)
- Updated documentation to reflect current authorization strategy and Docker Cloud configuration structure

### [Security]
- Implemented secrets-based password management using Docker Compose secrets
- Removed hardcoded password defaults from configuration files
- Added secure password generation using `openssl rand -base64 32`
- Added proper file permissions (600) for secret files
- Added `secrets/` directory to `.gitignore` to prevent accidental commits

### [Removed]
- Removed resource limits section from `docker-compose.yaml` (not in PRD requirements)
- Removed hardcoded password defaults from environment variables

## [Initial Release]

### [Added]
- Initial Jenkins setup with Docker Compose
- Jenkins Configuration as Code (JCasC) support
- Pre-installed plugins:
  - Configuration as Code
  - Matrix Authorization Strategy
  - Blue Ocean
  - Workflow Aggregator
  - Git
  - Docker Plugin
  - Docker Workflow
- Multi-architecture support (ARM64 and AMD64)
- Docker-in-Docker support via socket mounting
- Health check configuration
- Log rotation configuration
- Admin and regular user accounts
- Comprehensive test suite (`test_jenkins.py`)
- Documentation files:
  - `README.md`
  - `JENKINS_CONFIG.md`
  - `DOCKER_COMPOSE_CONFIG.md`
  - `TEST_README.md`
- Multi-architecture build script (`build-multiarch.sh`)
