# DYNAMIC DOCKER SOCK PATH SETTING

> Make this fully portable by deriving the Docker socket path from the active
> Docker context, then writing it into `.env` so `docker compose` uses it automatically.

Right now compose hard-codes `/var/run/docker.sock`  and the bash script only
writes `JENKINS_URL` + `JENKINS_ADMIN_EMAIL` to `.env` . We will:

1. Update `docker-compose.yaml` to mount `${DOCKER_SOCK_PATH}` instead of `/var/run/docker.sock`.
2. Update `setup-jenkins.sh` to:

   - read the Docker daemon endpoint via `docker context inspect`
   - extract the unix socket path
   - validate it exists
   - write `DOCKER_SOCK_PATH=...` into `.env` (in addition to the existing vars)

This works on:

- Ubuntu with Docker Engine (usually `unix:///var/run/docker.sock`)
- macOS with Colima (usually `unix:///Users/<user>/.colima/default/docker.sock`,
depending on profile/context)
- any other environment where the Docker CLI points to a unix socket via context

## 1) Change `docker-compose.yaml`

Replace the current socket mount line:

```yaml
      - /var/run/docker.sock:/var/run/docker.sock
```

With:

```yaml
      - ${DOCKER_SOCK_PATH}:/var/run/docker.sock
```

### Full updated `docker-compose.yaml` (complete file)

```yaml
services:
  jenkins:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: jenkins

    # Root is used so the container can access the docker socket reliably
    user: root

    ports:
      - "8080:8080"
      - "50000:50000"

    volumes:
      - jenkins_home:/var/jenkins_home
      - ./jenkins.yaml:/var/jenkins_home/casc_configs/jenkins.yaml:ro
      - ${DOCKER_SOCK_PATH}:/var/run/docker.sock

    secrets:
      - jenkins_admin_password
      - jenkins_devops_password

    environment:
      - JENKINS_OPTS=--httpPort=8080
      - CASC_JENKINS_CONFIG=/var/jenkins_home/casc_configs

      # Provided via .env written by setup-jenkins.sh
      - JENKINS_URL=${JENKINS_URL}
      - JENKINS_ADMIN_EMAIL=${JENKINS_ADMIN_EMAIL}

    command: >
      bash -lc '
        export PATH="/opt/java/openjdk/bin:$PATH";
        export JENKINS_ADMIN_PASSWORD="$(cat /run/secrets/jenkins_admin_password)";
        export JENKINS_DEVOPS_PASSWORD="$(cat /run/secrets/jenkins_devops_password)";
        exec /usr/local/bin/jenkins.sh
      '

    restart: unless-stopped

    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/login"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

    networks:
      - jenkins-network

secrets:
  jenkins_admin_password:
    file: ./secrets/jenkins_admin_password
  jenkins_devops_password:
    file: ./secrets/jenkins_devops_password

volumes:
  jenkins_home:
    driver: local

networks:
  jenkins-network:
    driver: bridge
```

## 2) Change `setup-jenkins.sh` to auto-detect DOCKER_SOCK_PATH

Your script already has a solid structure and writes `.env`.
Add a function to resolve the socket path from the active context and then
include it in `.env`.

### Drop-in code to add (place after “Prerequisites check passed.”)

Add this immediately after: `print_info "Prerequisites check passed."`

```bash
# Detect Docker socket path from the active Docker context
print_info "Detecting Docker socket from active Docker context..."

DOCKER_HOST_RAW="$(docker context inspect --format '{{.Endpoints.docker.Host}}' 2>/dev/null || true)"

if [ -z "$DOCKER_HOST_RAW" ]; then
    print_error "Failed to detect Docker host from docker context. Is Docker configured correctly?"
    exit 1
fi

case "$DOCKER_HOST_RAW" in
  unix://*)
    DOCKER_SOCK_PATH="${DOCKER_HOST_RAW#unix://}"
    ;;
  *)
    print_error "Docker context host is not a unix socket: $DOCKER_HOST_RAW"
    print_error "This setup expects a unix socket (works with Docker Engine and Colima)."
    exit 1
    ;;
esac

if [ ! -S "$DOCKER_SOCK_PATH" ]; then
    print_error "Detected docker socket path is not a socket: $DOCKER_SOCK_PATH"
    print_error "Docker Host from context was: $DOCKER_HOST_RAW"
    exit 1
fi

print_info "Using Docker socket path: $DOCKER_SOCK_PATH"
```

### Update the `.env` write to include DOCKER_SOCK_PATH

Replace your existing `.env` generation block:

```bash
cat > .env <<EOF
JENKINS_URL=${JENKINS_URL}
JENKINS_ADMIN_EMAIL=${JENKINS_ADMIN_EMAIL}
EOF
```

With:

```bash
cat > .env <<EOF
JENKINS_URL=${JENKINS_URL}
JENKINS_ADMIN_EMAIL=${JENKINS_ADMIN_EMAIL}
DOCKER_SOCK_PATH=${DOCKER_SOCK_PATH}
EOF
```

### Full updated `setup-jenkins.sh` (complete file)

```bash
#!/bin/bash

# Jenkins Setup Script
# This script automates the setup and deployment of Jenkins using Docker Compose
# with secrets-based password management.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
print_info "Checking prerequisites..."

if ! command_exists docker; then
    print_error "Docker is not installed. Please install Docker."
    exit 1
fi

if ! docker info >/dev/null 2>&1; then
    print_error "Docker service is not running. Please start Docker."
    exit 1
fi

if ! command_exists docker-compose && ! docker compose version >/dev/null 2>&1; then
    print_error "Docker Compose is not installed. Please install Docker Compose."
    exit 1
fi

print_info "Prerequisites check passed."

# Detect Docker socket path from the active Docker context
print_info "Detecting Docker socket from active Docker context..."

DOCKER_HOST_RAW="$(docker context inspect --format '{{.Endpoints.docker.Host}}' 2>/dev/null || true)"

if [ -z "$DOCKER_HOST_RAW" ]; then
    print_error "Failed to detect Docker host from docker context. Is Docker configured correctly?"
    exit 1
fi

case "$DOCKER_HOST_RAW" in
  unix://*)
    DOCKER_SOCK_PATH="${DOCKER_HOST_RAW#unix://}"
    ;;
  *)
    print_error "Docker context host is not a unix socket: $DOCKER_HOST_RAW"
    print_error "This setup expects a unix socket (works with Docker Engine and Colima)."
    exit 1
    ;;
esac

if [ ! -S "$DOCKER_SOCK_PATH" ]; then
    print_error "Detected docker socket path is not a socket: $DOCKER_SOCK_PATH"
    print_error "Docker Host from context was: $DOCKER_HOST_RAW"
    exit 1
fi

print_info "Using Docker socket path: $DOCKER_SOCK_PATH"

# Prompt for JENKINS_URL
read -p "Enter Jenkins URL [http://localhost:8080/]: " JENKINS_URL_INPUT
JENKINS_URL=${JENKINS_URL_INPUT:-http://localhost:8080/}

# Ensure URL ends with /
if [[ ! "$JENKINS_URL" =~ /$ ]]; then
    JENKINS_URL="${JENKINS_URL}/"
fi

# Prompt for JENKINS_ADMIN_EMAIL
read -p "Enter Jenkins admin email [admin@example.com]: " JENKINS_ADMIN_EMAIL_INPUT
JENKINS_ADMIN_EMAIL=${JENKINS_ADMIN_EMAIL_INPUT:-admin@example.com}

# Validate inputs
if [ -z "$JENKINS_URL" ]; then
    print_error "JENKINS_URL cannot be empty."
    exit 1
fi

if [ -z "$JENKINS_ADMIN_EMAIL" ]; then
    print_error "JENKINS_ADMIN_EMAIL cannot be empty."
    exit 1
fi

print_info "Using Jenkins URL: $JENKINS_URL"
print_info "Using admin email: $JENKINS_ADMIN_EMAIL"

# Create secrets directory
print_info "Creating secrets directory..."
mkdir -p secrets
chmod 700 secrets

# Generate passwords
print_info "Generating secure passwords..."

# Check if secrets already exist
if [ -f "secrets/jenkins_admin_password" ] || [ -f "secrets/jenkins_devops_password" ]; then
    print_warn "Secret files already exist. They will be regenerated."
fi

# Generate admin password
if command_exists openssl; then
    openssl rand -base64 32 > secrets/jenkins_admin_password
    openssl rand -base64 32 > secrets/jenkins_devops_password
else
    print_error "openssl is not installed. Cannot generate secure passwords."
    exit 1
fi

# Set proper permissions
chmod 600 secrets/jenkins_admin_password
chmod 600 secrets/jenkins_devops_password

print_info "Passwords generated and stored securely."

# Create/update .env file
print_info "Creating .env file..."
cat > .env <<EOF
JENKINS_URL=${JENKINS_URL}
JENKINS_ADMIN_EMAIL=${JENKINS_ADMIN_EMAIL}
DOCKER_SOCK_PATH=${DOCKER_SOCK_PATH}
EOF

print_info ".env file created."

# Ask if user wants to build
read -p "Do you want to build the image before running? [y/N]: " BUILD_INPUT
BUILD_FLAG=""
if [[ "$BUILD_INPUT" =~ ^[Yy]$ ]]; then
    BUILD_FLAG="--build"
    print_info "Will build image before starting."
else
    print_info "Will use existing image (if available)."
fi

# Check if containers are already running
if docker ps --filter "name=jenkins" --format "{{.Names}}" | grep -q "^jenkins$"; then
    print_warn "Jenkins container is already running."
    read -p "Do you want to stop and remove existing containers before starting? [y/N]: " STOP_INPUT
    if [[ "$STOP_INPUT" =~ ^[Yy]$ ]]; then
        print_info "Stopping existing containers..."
        docker compose down
    fi
fi

# Start Jenkins
print_info "Starting Jenkins..."
if docker compose up -d $BUILD_FLAG; then
    print_info "Jenkins is starting..."
    print_info "Waiting for Jenkins to be ready..."

    # Wait for Jenkins to be ready (up to 2 minutes)
    MAX_WAIT=120
    ELAPSED=0
    while [ $ELAPSED -lt $MAX_WAIT ]; do
        if curl -sf http://localhost:8080/login >/dev/null 2>&1; then
            print_info "Jenkins is ready!"
            break
        fi
        sleep 2
        ELAPSED=$((ELAPSED + 2))
        echo -n "."
    done
    echo ""

    if [ $ELAPSED -ge $MAX_WAIT ]; then
        print_warn "Jenkins may still be starting. Check logs with: docker logs jenkins"
    fi

    print_info "=========================================="
    print_info "Jenkins setup complete!"
    print_info "=========================================="
    print_info "Jenkins URL: $JENKINS_URL"
    print_info "Admin email: $JENKINS_ADMIN_EMAIL"
    print_info ""
    print_info "Login credentials:"
    print_info "  Username: admin"
    print_info "  Password: (stored in secrets/jenkins_admin_password)"
    print_info ""
    print_info "  Username: devops"
    print_info "  Password: (stored in secrets/jenkins_devops_password)"
    print_info ""
    print_info "To view logs: docker logs -f jenkins"
    print_info "To stop Jenkins: docker compose down"
    print_info "=========================================="
else
    print_error "Failed to start Jenkins. Check logs with: docker logs jenkins"
    exit 1
fi
```

This is your existing script  with only:

- the docker context detection added
- `DOCKER_SOCK_PATH` appended to `.env`

## 3) Commands to run (in order)

From your repo root:

```bash
# 1) Make sure compose file is updated to use ${DOCKER_SOCK_PATH}
#    and script is updated as shown above.

# 2) Run setup
chmod +x setup-jenkins.sh
./setup-jenkins.sh
```

That is it. The script will:

- derive the correct socket path from the active Docker context
- generate secrets
- write `.env` with URL/email/socket
- run `docker compose up`

## Important note about Docker contexts

This works if your active context points to a **unix** socket (Docker Engine, Colima).
If you ever switch to a TCP endpoint (for example remote Docker daemon), the script
will intentionally fail with a clear error, because your compose mounts a local
file socket into the container and that is not meaningful for TCP endpoints.
