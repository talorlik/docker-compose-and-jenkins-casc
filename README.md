# docker-compose-and-jenkins-casc

> [!NOTE]
> This repository demonstrates how to create a Jenkins server using Docker Compose
> and Jenkins Configuration as Code (JCasC). The setup includes plugins, and supports
> both ARM and AMD architectures.

## Features

- ✅ Jenkins running in Docker
- ✅ Configuration as Code (JCasC) for automated setup
- ✅ Pre-installed plugins:
  - Blue Ocean
  - Docker Pipeline
  - Configuration as Code
  - Docker Plugin
  - Workflow Aggregator
  - Matrix Authorization Strategy
- ✅ Multi-architecture support (ARM64 and AMD64)
- ✅ Pre-configured admin and devops users
- ✅ Secrets-based password management
- ✅ Automated setup script
- ✅ Docker-in-Docker support

## Prerequisites

- Docker Engine 20.10 or later
- Docker Compose 2.0 or later
- For multi-arch builds: Docker Buildx (included with Docker Desktop)

## Quick Start

### Automated Setup (Recommended)

Use the `setup-jenkins.sh` script for automated setup:

```bash
./setup-jenkins.sh
```

The script will:

- Prompt for Jenkins URL and admin email
- Generate secure passwords automatically
- Create the `.env` file
- Optionally build the image
- Start Jenkins with Docker Compose

### Manual Setup

#### 1. Create Secrets

Create the secrets directory and generate secure passwords:

```bash
mkdir -p secrets
chmod 700 secrets
openssl rand -base64 32 > secrets/jenkins_admin_password
openssl rand -base64 32 > secrets/jenkins_devops_password
chmod 600 secrets/jenkins_admin_password secrets/jenkins_devops_password
```

#### 2. Create `.env` File

**Recommended**: Use `setup-jenkins.sh` which automatically detects the Docker
socket path and creates the `.env` file. The script handles:
- Detection of Docker socket from active Docker context
- Special handling for VM-based Docker (Colima/Lima) environments
- Automatic validation of socket path

Alternatively, create a `.env` file manually with required configuration:

```bash
# Detect Docker socket path from active Docker context
DOCKER_HOST_RAW=$(docker context inspect --format '{{.Endpoints.docker.Host}}')
DOCKER_SOCK_PATH="${DOCKER_HOST_RAW#unix://}"

# For VM-based Docker (Colima/Lima), use /var/run/docker.sock in container
# For native Docker Engine, use the detected path
if [[ "$DOCKER_SOCK_PATH" == *".colima/"* ]] || [[ "$DOCKER_SOCK_PATH" == *".lima/"* ]]; then
    DOCKER_SOCK_PATH="/var/run/docker.sock"
fi

cat > .env <<EOF
JENKINS_URL=http://localhost:8080/
JENKINS_ADMIN_EMAIL=admin@example.com
DOCKER_SOCK_PATH=${DOCKER_SOCK_PATH}
EOF
```

**Note**: The Docker socket path is automatically detected from your active
Docker context. The setup script handles different Docker environments:
- **Native Docker Engine**: Uses the detected socket path directly
- **VM-based Docker (Colima/Lima)**: Automatically uses `/var/run/docker.sock` as the container path
- On macOS with Colima, the host path might be `/Users/<user>/.colima/default/docker.sock`

#### 3. Build and Start Jenkins

For single architecture (your current platform):

```bash
docker compose up -d --build
```

> **NOTE:**
>
> - Use the `-d` flag to run as a daemon.
> - Use the `--build` flag to force a rebuild of the image.

For multi-architecture support (ARM64 and AMD64):

```bash
# Build for multiple architectures
./build-multiarch.sh

# Start with docker compose
docker compose up -d
```

> [!NOTE]
> The `build-multiarch.sh` script builds the Jenkins image for both `linux/amd64`
> and `linux/arm64` platforms. The built image is tagged as `jenkins/jenkins:latest-jdk21`.
> The `--load` flag loads the image into the local Docker daemon (note: only one
> platform can be loaded at a time).
>
>
> For detailed information about the Docker Compose configuration, see [DOCKER_COMPOSE_CONFIG.md](DOCKER_COMPOSE_CONFIG.md).

### 4. Access Jenkins

1. Open your browser and navigate to: `http://localhost:8080`
2. Login with:
   - **Username**: `admin`
   - **Password**: (stored in `secrets/jenkins_admin_password`)

   Or:
   - **Username**: `devops`
   - **Password**: (stored in `secrets/jenkins_devops_password`)

To view passwords:

```bash
cat secrets/jenkins_admin_password
cat secrets/jenkins_devops_password
```

### 4. Verify Installation

- Blue Ocean should be accessible at: `http://localhost:8080/blue`
- Docker Pipeline plugin should be available in pipeline configurations
- Configuration as Code plugin should show the applied configuration

## Configuration

### Jenkins Configuration as Code

The Jenkins configuration is defined in `jenkins.yaml`. This file includes:

- **Security Realm**: Local user authentication with admin and devops users
- **Authorization**: Role-based access control with fine-grained permissions
- **Docker Cloud**: Configured for dynamic agent provisioning via Docker socket
- **System Settings**: Admin email, URL, and other system configurations (loaded
from environment variables)

For a detailed explanation of each configuration option, see [JENKINS_CONFIG.md](JENKINS_CONFIG.md).

### Customizing Configuration

Edit `jenkins.yaml` to customize:

- User accounts and permissions
- Jenkins system settings
- Docker cloud configuration
- Global libraries
- Tool installations

**Important**: Passwords are managed through Docker Compose secrets stored in the
`secrets/` directory. To change passwords, regenerate the secret files and restart
Jenkins:

```bash
openssl rand -base64 32 > secrets/jenkins_admin_password
openssl rand -base64 32 > secrets/jenkins_devops_password
docker compose restart jenkins
```

After making configuration changes, restart Jenkins:

```bash
docker compose restart jenkins
```

## Docker-in-Docker

This setup includes Docker-in-Docker support, allowing Jenkins pipelines to build
Docker images. The Docker socket is mounted from the host, enabling Jenkins to
use the host's Docker daemon.

**Note**: The Jenkins container runs as the `jenkins` user (non-root) with docker
group membership for secure Docker socket access. For production environments,
consider using Docker-in-Docker containers or a separate Docker daemon.

## Docker Cloud

Docker Cloud is a Jenkins feature that allows Jenkins to dynamically provision
Docker containers as build agents on demand, rather than using static build agents.

### What it does

Instead of maintaining permanent build agents, Jenkins can:

- **Spin up Docker containers** as build agents when jobs need them
- **Run builds in isolated containers** with clean environments
- **Automatically tear down containers** when builds complete (after idle timeout)
- **Scale agents dynamically** based on workload

### How it works in this setup

The Docker Cloud is configured in `jenkins.yaml` with the following settings:

- **Instance Cap**: Up to 10 containers can run simultaneously
- **Agent Image**: Uses `jenkins/inbound-agent:lts-jdk21` for build agents
- **Label**: Jobs can request agents with the `docker` label
- **Idle Timeout**: Agents are removed after 5 minutes of inactivity
- **Docker Socket**: Connects to host Docker daemon via dynamically detected
socket path (automatically detected from Docker context)

### Example use case

When a Jenkins pipeline specifies:

```groovy
pipeline {
    agent {
        label 'docker'
    }
    // ...
}
```

Jenkins will automatically:

1. Create a Docker container from the configured agent image
2. Run the build inside that container
3. Remove the container when the build completes

### Benefits

- **Isolation**: Each build runs in a clean, isolated container
- **Resource Efficiency**: Agents only exist during builds, saving resources
- **Consistency**: Every build gets the same environment
- **Scalability**: Automatically creates agents as needed without manual setup

### When you need it

You need Docker Cloud if you want:

- Dynamic, on-demand build agents
- Isolated build environments per job
- Different tool versions or environments for different jobs
- Automatic scaling based on workload

You don't need it if:

- You only run builds on the Jenkins master node
- You use static, pre-configured build agents
- You don't need isolated build environments

## Volumes

- `jenkins_home`: Persistent storage for Jenkins data, configurations, and build
history
- `jenkins.yaml`: Mounted as read-only configuration file for JCasC

## Ports

- `8080`: Jenkins web interface
- `50000`: Jenkins agent communication port

## Troubleshooting

### Jenkins won't start

1. Check logs: `docker compose logs jenkins`
2. Verify Docker socket permissions: The Jenkins container runs as the `jenkins`
user with docker group membership.
   The socket should be owned by `root:docker` with permissions `srw-rw----`
   (typically mode `0660`). Check with: `ls -l $DOCKER_SOCK_PATH`
   (or check your `.env` file for the detected path)
3. Verify Docker group GID: The container's docker group uses GID 999 (standard).
If your host's docker group has a different GID, you may need to adjust the Dockerfile
or ensure the socket has appropriate permissions.
4. Ensure ports `8080` and `50000` are not in use
5. Verify Docker socket path: Check that `DOCKER_SOCK_PATH` in `.env` points to
a valid socket file. For VM-based Docker (Colima/Lima), the path should be
`/var/run/docker.sock` (the container-side path).
6. Check Java PATH: The container sets `PATH="/opt/java/openjdk/bin:$PATH"` to ensure
Java tools are accessible. If you see Java-related errors, verify the JDK installation
in the container.

### Configuration not applied

1. Check JCasC logs in Jenkins: `Manage Jenkins` → `System Log` →
`Configuration as Code`
2. Verify `jenkins.yaml` syntax is correct
3. Ensure the configuration file is mounted correctly

### Multi-arch build issues

1. Ensure Docker Buildx is installed: `docker buildx version`
2. Create a new builder: `docker buildx create --name multiarch --use`
3. Inspect builder: `docker buildx inspect --bootstrap`

## Tests

This repository includes comprehensive unit tests for the Jenkins configuration,
covering:

- User authentication (admin and regular users)
- Admin permissions (Overall/Administer)
- User permissions (Job/Read, Job/Build, Job/Cancel, Job/Workspace, View/Read)
- Container health checks

For detailed information about running and maintaining the tests, see [TEST_README.md](TEST_README.md).

## Stopping Jenkins

```bash
docker compose down
```

To remove volumes (⚠️ this deletes all Jenkins data):

```bash
docker compose down -v
```

## License

See [LICENSE](LICENSE) file for details.
