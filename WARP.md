# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This repository demonstrates a Jenkins server setup using Docker Compose and Jenkins
Configuration as Code (JCasC). It supports multi-architecture builds (ARM64/AMD64)
and provides Docker-in-Docker capabilities for pipeline builds.

## Architecture

### Core Components

- **Dockerfile**: Multi-stage build that installs Docker CLI, updates packages
for security, and installs Jenkins plugins via `jenkins-plugin-cli`
- **docker-compose.yaml**: Defines the Jenkins service with volumes, networking,
health checks, resource limits, and Docker socket mounting
- **jenkins.yaml**: JCasC configuration defining security realms, authorization
(matrix-based), Docker cloud agents, system settings, and tool installations
- **plugins.txt**: List of Jenkins plugins to be installed (Configuration as Code,
Matrix Auth, Blue Ocean, Docker Workflow, Docker Plugin, Workflow Aggregator)

### Key Configuration Details

- **Security**: Uses local security realm with two users (admin/user) with
role-based permissions via global matrix authorization
- **Docker Cloud**: Configured to dynamically provision Docker containers as
build agents on demand (up to 10 containers, 5 per template)
- **Docker-in-Docker**: Host Docker socket (dynamically detected from Docker context)
is mounted into the container at `/var/run/docker.sock`, allowing Jenkins to build
Docker images. Container runs as the `jenkins` user (added to docker group) for
secure socket access without root privileges. The socket path is automatically
detected by `setup-jenkins.sh` from the active Docker context.
- **Multi-arch Support**: `build-multiarch.sh` uses Docker Buildx to create
images for both linux/amd64 and linux/arm64

### Environment Variables

- `JENKINS_ADMIN_PASSWORD`: Admin user password (default: admin123)
- `JENKINS_USER_PASSWORD`: Regular user password (default: user123)
- `JENKINS_ADMIN_EMAIL`: Admin email for system configuration (default: <admin@example.com>)

## Common Commands

### Building and Running

```bash
# Start Jenkins (single architecture)
docker compose up

# Start Jenkins in background
docker compose up -d

# Force rebuild of image
docker compose up --build

# Build multi-architecture image (ARM64 + AMD64)
./build-multiarch.sh

# Stop Jenkins
docker compose down

# Stop and remove all data (⚠️ deletes jenkins_home volume)
docker compose down -v

# Restart Jenkins (e.g., after config changes)
docker compose restart jenkins

# View logs
docker compose logs jenkins

# Follow logs in real-time
docker compose logs -f jenkins
```

### Testing

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests (requires Jenkins to be running)
pytest test_jenkins.py -v

# Run specific test class
pytest test_jenkins.py::TestJenkinsAuthentication -v
pytest test_jenkins.py::TestAdminPermissions -v
pytest test_jenkins.py::TestUserPermissions -v
pytest test_jenkins.py::TestContainerHealthCheck -v

# Run specific test case
pytest test_jenkins.py::TestJenkinsAuthentication::test_admin_login_success -v

# Test with custom Jenkins instance
JENKINS_URL=http://jenkins.example.com:8080 pytest test_jenkins.py -v

# Test with custom passwords
JENKINS_ADMIN_PASSWORD=mypass JENKINS_USER_PASSWORD=userpass pytest test_jenkins.py -v
```

### Debugging

```bash
# Check container health
docker ps --filter name=jenkins

# Check Docker socket permissions (should be srw-rw---- root:docker)
# Check your .env file for DOCKER_SOCK_PATH, or use:
ls -l ${DOCKER_SOCK_PATH:-/var/run/docker.sock}

# Verify multi-arch builder setup
docker buildx version
docker buildx inspect multiarch --bootstrap

# Access Jenkins web interface
open http://localhost:8080

# Access Blue Ocean UI
open http://localhost:8080/blue
```

## Development Workflow

### Modifying Jenkins Configuration

1. Edit `jenkins.yaml` with desired changes (users, permissions, Docker cloud
settings, etc.)
2. Restart Jenkins to apply: `docker compose restart jenkins`
3. Verify configuration was applied: Navigate to Manage Jenkins → Configuration
as Code in the web UI
4. Check for JCasC errors: Manage Jenkins → System Log → Configuration as Code

### Adding Jenkins Plugins

1. Add plugin to `plugins.txt` (format: `plugin-id:version` or `plugin-id:latest`)
2. Rebuild image: `docker compose up --build`
3. Verify plugin installation in Jenkins web UI

### Multi-Architecture Development

The `build-multiarch.sh` script:

- Checks for Docker and Docker Buildx availability
- Creates/uses a buildx builder named "multiarch"
- Builds for both linux/amd64 and linux/arm64
- Tags image as `jenkins/jenkins:latest-jdk21`
- Note: `--load` flag only loads one platform at a time into local Docker daemon

## Testing Strategy

The test suite (`test_jenkins.py`) validates:

- Admin and regular user authentication
- Permission model (admin has Overall/Administer, user has limited Job/View permissions)
- Container health check functionality
- Configuration as Code application

Tests use Jenkins REST API with CSRF protection (crumb issuer). Temporary test
jobs are created with `test-job-*` prefix and cleaned up after testing.

## Security Considerations

- Jenkins runs as the `jenkins` user (non-root) with docker group membership for
Docker socket access
- Default passwords should be changed via environment variables or `.env` file
- For production: Consider using separate Docker daemon instead of mounting
host socket
- Docker socket permissions: Ensure the host docker socket has docker group
permissions (typically GID 999)
- Always run Snyk code scans on new or modified code to identify security issues
- Fix security issues immediately and rescan until clean

## Service Details

- **Web Interface**: Port 8080
- **Agent Communication**: Port 50000
- **Health Check**: Polls `http://localhost:8080/login` every 30s
- **Resource Limits**: 2 CPU cores max, 4GB memory max
- **Resource Reservations**: 1 CPU core, 2GB memory
- **Logging**: JSON file driver with 10MB max size, 3 file rotation
