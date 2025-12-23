# RUN JENKINS SERVER WITH DOCKER COMPOSE

> Below is a complete, consolidated setup that is robust, boots cleanly, meets
> the "no hard-coded passwords" requirement, and includes Docker Cloud
> configuration in JCasC.

You will end up with these files:

- `Dockerfile` (builds a Jenkins image with plugins preinstalled)
- `plugins.txt` (plugin list)
- `jenkins.yaml` (JCasC, includes Docker Cloud + two users)
- `docker-compose.yaml` (uses Docker Compose secrets + env mapping, no
hard-coded passwords)
- `.env` (non-secret variables, not committed)
- `.gitignore` (exclude secrets and .env)

## Target directory layout

```text
.
├─ Dockerfile
├─ docker-compose.yaml
├─ jenkins.yaml
├─ plugins.txt
├─ .env                 # not committed
├─ .gitignore
└─ secrets/             # not committed
   ├─ jenkins_admin_password
   └─ jenkins_devops_password
```

## File 1: Dockerfile

This builds Jenkins and installs plugins at build-time (more reliable than
"install on first boot").

```dockerfile
# Stage 1: Base image with system packages
FROM jenkins/jenkins:latest-jdk21 AS base

USER root

# Install Docker CLI, curl (for healthcheck), and update all packages to fix vulnerabilities
RUN apt-get update && \
    apt-get upgrade -y --no-install-recommends && \
    apt-get install -y --no-install-recommends docker.io curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Stage 2: Install Jenkins plugins
FROM base AS plugins

# Copy plugins file
COPY plugins.txt /usr/share/jenkins/ref/plugins.txt

# Install plugins
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt

# Stage 3: Final image
FROM plugins

# Add jenkins user to docker group to access Docker socket without root
# The docker group GID will match the host's docker group when the socket is mounted
RUN groupadd -g 999 docker 2>/dev/null || true && \
    usermod -aG docker jenkins

USER jenkins
```

## File 2: plugins.txt

This includes the plugins you need for:

- JCasC
- Matrix authorization
- Pipelines
- Git
- Docker Cloud (agents)

```txt
configuration-as-code:latest
matrix-auth:latest
blueocean:latest
workflow-aggregator:latest
git:latest

docker-plugin:latest
docker-workflow:latest
```

## File 3: jenkins.yaml (JCasC)

This includes:

- `admin` user (password from env var)
- `devops` user (password from env var)
- Docker Cloud configuration (socket-based)
- Location config (`JENKINS_URL`, `JENKINS_ADMIN_EMAIL`) from env vars
- Conservative matrix permissions

```yaml
jenkins:
  systemMessage: "Jenkins configured automatically by Jenkins Configuration as Code"

  numExecutors: 2
  mode: NORMAL

  crumbIssuer:
    standard:
      excludeClientIPFromCrumb: false

  disableRememberMe: false

  securityRealm:
    local:
      allowsSignup: false
      enableCaptcha: false
      users:
        - id: "admin"
          name: "Jenkins Admin"
          password: "${JENKINS_ADMIN_PASSWORD}"
        - id: "devops"
          name: "DevOps User"
          password: "${JENKINS_DEVOPS_PASSWORD}"

  authorizationStrategy:
    globalMatrix:
      permissions:
        - "Overall/Administer:admin"

        - "Overall/Read:authenticated"
        - "Job/Read:authenticated"
        - "Job/Build:authenticated"
        - "Job/Cancel:authenticated"
        - "Job/Workspace:authenticated"
        - "View/Read:authenticated"

        - "Agent/Connect:authenticated"
        - "Agent/Disconnect:authenticated"
        - "Run/Replay:authenticated"
        - "Run/Update:authenticated"

  clouds:
    - docker:
        name: "docker"
        dockerApi:
          dockerHost:
            uri: "unix:///var/run/docker.sock"
          connectTimeout: 60
          readTimeout: 60

        templates:
          - dockerTemplate:
              labelString: "docker"
              instanceCapStr: "10"
              mode: NORMAL
              remoteFs: "/home/jenkins/agent"

              dockerTemplateBase:
                image: "jenkins/inbound-agent:lts-jdk21"
                pullStrategy: PULL_LATEST

              connector:
                attach:
                  user: "jenkins"

              retentionStrategy:
                idleMinutes: 5

unclassified:
  location:
    url: "${JENKINS_URL}"
    adminAddress: "${JENKINS_ADMIN_EMAIL}"

tool:
  git:
    installations:
      - name: "Default"
        home: "git"
```

Notes:

- This uses the Docker socket. The Docker socket path is dynamically detected
from your active Docker context and mounted into the container at `/var/run/docker.sock`
(inside the container). The host path is automatically detected by `setup-jenkins.sh`.
- Works with Docker Engine (typically `/var/run/docker.sock`) and Colima on macOS
(typically `/Users/<user>/.colima/default/docker.sock`).
- The Jenkins container runs as the `jenkins` user (non-root) with docker group
membership for secure Docker socket access. The docker group uses GID 999 (standard).
If your host's docker group has a different GID, you may need to adjust the Dockerfile.
- If Jenkins fails to start due to schema mismatch, you will see a clear JCasC
error in logs. In that case, the fix is to align the YAML keys to your installed
`docker-plugin` version (I can do that from the exact error).

## File 4: docker-compose.yaml

This:

- Mounts Docker socket (dynamically detected from Docker context)
- Mounts the JCasC file
- Uses Docker Compose secrets for passwords (no hard-coded values)
- Exports secrets into env vars right before Jenkins starts
- Requires `JENKINS_URL`, `JENKINS_ADMIN_EMAIL`, and `DOCKER_SOCK_PATH` to be
provided externally (via `.env` or shell export)

```yaml
services:
  jenkins:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: jenkins

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

    # Load secrets into env vars for JCasC substitution, then start Jenkins
    command: >
      bash -lc '
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

## File 5: .env (non-secret, not committed)

Create this locally. Do not commit it. The `setup-jenkins.sh` script automatically
detects the Docker socket path and creates this file.

```bash
JENKINS_URL=http://localhost:8080/
JENKINS_ADMIN_EMAIL=admin@example.com
DOCKER_SOCK_PATH=/var/run/docker.sock
```

**Note**: `DOCKER_SOCK_PATH` is automatically detected from your active Docker
context by `setup-jenkins.sh`. On macOS with Colima, this might be something
like `/Users/<user>/.colima/default/docker.sock`.

## File 6: .gitignore

Add these lines:

```gitignore
.env
secrets/
```

## Commands to run, in order

### 0) Optional: start clean (recommended after previous failure)

This removes your Jenkins home volume (jobs/config will be wiped).

```bash
docker compose down -v
```

If you want to preserve existing Jenkins data, do not use `-v`.

### 1) Create secrets (passwords) locally

```bash
mkdir -p secrets
chmod 700 secrets

openssl rand -base64 32 > secrets/jenkins_admin_password
openssl rand -base64 32 > secrets/jenkins_devops_password

chmod 600 secrets/jenkins_admin_password secrets/jenkins_devops_password
```

To rotate passwords later, overwrite the files and restart Jenkins.

### 2) Create `.env` (or export vars in your shell)

**Recommended**: Use `setup-jenkins.sh` which automatically detects the Docker
socket path and creates the `.env` file.

Option A: Use setup script (recommended)

```bash
./setup-jenkins.sh
```

The script will:

- Detect Docker socket path from active Docker context
- Prompt for Jenkins URL and admin email
- Generate secure passwords
- Create `.env` file with all required variables

Option B: Manual `.env` creation

```bash
# First, detect Docker socket path
DOCKER_SOCK_PATH=$(docker context inspect --format '{{.Endpoints.docker.Host}}' | sed 's|unix://||')

cat > .env <<EOF
JENKINS_URL=http://localhost:8080/
JENKINS_ADMIN_EMAIL=admin@example.com
DOCKER_SOCK_PATH=${DOCKER_SOCK_PATH}
EOF
```

Option C: export in shell (no file)

```bash
DOCKER_SOCK_PATH=$(docker context inspect --format '{{.Endpoints.docker.Host}}' | sed 's|unix://||')
export JENKINS_URL="http://localhost:8080/"
export JENKINS_ADMIN_EMAIL="admin@example.com"
export DOCKER_SOCK_PATH="${DOCKER_SOCK_PATH}"
```

### 3) Build and start Jenkins

```bash
docker compose up -d --build
```

### 4) Verify Jenkins is healthy

Follow logs:

```bash
docker logs -f jenkins
```

Confirm plugins exist:

```bash
docker exec -it jenkins ls -1 /var/jenkins_home/plugins | sed 's/\.jpi$//;s/\.hpi$//' | sort
```

Confirm Docker Cloud is configured:

- In Jenkins UI: **Manage Jenkins -> Nodes and Clouds -> Clouds**
- Or check logs for JCasC apply completion.

## How to use the Docker cloud in a Pipeline

Example Jenkinsfile:

```groovy
pipeline {
  agent { label 'docker' }
  stages {
    stage('Smoke') {
      steps {
        sh 'uname -a'
        sh 'id'
      }
    }
  }
}
```

## If it still restart-loops

Docker Cloud JCasC is the most schema-sensitive section. If Jenkins fails, run:

```bash
docker logs jenkins | tail -n 200
```
