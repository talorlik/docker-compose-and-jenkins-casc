# docker-compose-and-jenkins-casc

This repository demonstrates how to create a Jenkins server using Docker Compose and Jenkins Configuration as Code (JCasC). The setup includes Blue Ocean, Docker Pipeline, and Configuration as Code plugins, with support for both ARM and AMD architectures.

## Features

- ✅ Jenkins LTS running in Docker
- ✅ Configuration as Code (JCasC) for automated setup
- ✅ Pre-installed plugins:
  - Blue Ocean
  - Docker Pipeline
  - Configuration as Code
  - Docker Plugin
  - Workflow Aggregator
- ✅ Multi-architecture support (ARM64 and AMD64)
- ✅ Pre-configured admin user
- ✅ Docker-in-Docker support

## Prerequisites

- Docker Engine 20.10 or later
- Docker Compose 2.0 or later
- For multi-arch builds: Docker Buildx (included with Docker Desktop)

## Quick Start

### 1. Set Admin Password (Optional)

By default, the admin user password is `admin123`. To change it, set the `JENKINS_ADMIN_PASSWORD` environment variable in `docker-compose.yml` or create a `.env` file:

```bash
echo "JENKINS_ADMIN_PASSWORD=your-secure-password" > .env
```

### 2. Build and Start Jenkins

For single architecture (your current platform):

```bash
docker-compose up -d --build
```

For multi-architecture support (ARM64 and AMD64):

```bash
# Create a buildx builder (if not already created)
docker buildx create --name multiarch --use

# Build for multiple platforms
docker buildx build --platform linux/amd64,linux/arm64 -t jenkins-casc:latest --load .

# Start with docker-compose
docker-compose up -d
```

### 3. Access Jenkins

1. Open your browser and navigate to: `http://localhost:8080`
2. Login with:
   - **Username**: `admin`
   - **Password**: `admin123` (or your custom password)

### 4. Verify Installation

- Blue Ocean should be accessible at: `http://localhost:8080/blue`
- Docker Pipeline plugin should be available in pipeline configurations
- Configuration as Code plugin should show the applied configuration

## Configuration

### Jenkins Configuration as Code

The Jenkins configuration is defined in `jenkins.yaml`. This file includes:

- **Security Realm**: Local user authentication with admin user
- **Authorization**: Logged-in users can do anything
- **Docker Cloud**: Configured for Docker-in-Docker support
- **System Settings**: Admin email, URL, and other system configurations

### Customizing Configuration

Edit `jenkins.yaml` to customize:

- User accounts and permissions
- Jenkins system settings
- Docker cloud configuration
- Global libraries
- Tool installations

After making changes, restart Jenkins:

```bash
docker-compose restart jenkins
```

## Architecture Support

This setup supports both ARM64 (Apple Silicon, ARM-based servers) and AMD64 (Intel/AMD processors) architectures.

### Building Multi-Arch Images

To build and push multi-arch images:

```bash
# Build and push to registry
docker buildx build --platform linux/amd64,linux/arm64 \
  -t your-registry/jenkins-casc:latest \
  --push .
```

### Running on Different Architectures

The Docker Compose setup will automatically use the correct image for your platform. For explicit platform selection:

```bash
# For ARM64 (Apple Silicon)
docker-compose up -d --build --platform linux/arm64

# For AMD64 (Intel/AMD)
docker-compose up -d --build --platform linux/amd64
```

## Docker-in-Docker

This setup includes Docker-in-Docker support, allowing Jenkins pipelines to build Docker images. The Docker socket is mounted from the host, enabling Jenkins to use the host's Docker daemon.

**Note**: This requires the Jenkins container to run as root. For production environments, consider using Docker-in-Docker containers or a separate Docker daemon.

## Docker Cloud

Docker Cloud is a Jenkins feature that allows Jenkins to dynamically provision Docker containers as build agents on demand, rather than using static build agents.

### What it does

Instead of maintaining permanent build agents, Jenkins can:

- **Spin up Docker containers** as build agents when jobs need them
- **Run builds in isolated containers** with clean environments
- **Automatically tear down containers** when builds complete
- **Scale agents dynamically** based on workload

### How it works in this setup

The Docker Cloud is configured in `jenkins.yaml` with the following settings:

- **Container Cap**: Up to 10 total containers can be created
- **Instance Cap**: Up to 5 containers can run simultaneously per template
- **Agent Image**: Uses `jenkins/inbound-agent:latest` for build agents
- **Label**: Jobs can request agents with the `docker` label

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

- `jenkins_home`: Persistent storage for Jenkins data, configurations, and build history
- `jenkins.yaml`: Mounted as read-only configuration file for JCasC

## Ports

- `8080`: Jenkins web interface
- `50000`: Jenkins agent communication port

## Troubleshooting

### Jenkins won't start

1. Check logs: `docker-compose logs jenkins`
2. Verify Docker socket permissions: `ls -la /var/run/docker.sock`
3. Ensure ports 8080 and 50000 are not in use

### Configuration not applied

1. Check JCasC logs in Jenkins: `Manage Jenkins` → `System Log` → `Configuration as Code`
2. Verify `jenkins.yaml` syntax is correct
3. Ensure the configuration file is mounted correctly

### Multi-arch build issues

1. Ensure Docker Buildx is installed: `docker buildx version`
2. Create a new builder: `docker buildx create --name multiarch --use`
3. Inspect builder: `docker buildx inspect --bootstrap`

## Stopping Jenkins

```bash
docker-compose down
```

To remove volumes (⚠️ this deletes all Jenkins data):

```bash
docker-compose down -v
```

## License

See LICENSE file for details.
