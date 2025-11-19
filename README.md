# docker-compose-and-jenkins-casc

> [!INFO]
> This repository demonstrates how to create a Jenkins server using Docker Compose and Jenkins Configuration as Code (JCasC). The setup includes plugins, and supports both ARM and AMD architectures.

## Features

- ✅ Jenkins running in Docker
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

By default, the admin user password is `admin123`. To change it, set the `JENKINS_ADMIN_PASSWORD` environment variable in `docker-compose.yaml` or create a `.env` file:

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
# Run
./build-multiarch.sh

# Start with docker-compose
docker-compose up -d
```

> [!NOTE]
> For detailed information about the Docker Compose configuration, see [DOCKER_COMPOSE_CONFIG.md](DOCKER_COMPOSE_CONFIG.md).

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

- **Security Realm**: Local user authentication with admin and regular users
- **Authorization**: Role-based access control with fine-grained permissions
- **Docker Cloud**: Configured for Docker-in-Docker support
- **System Settings**: Admin email, URL, and other system configurations

For a detailed explanation of each configuration option, see [JENKINS_CONFIG.md](JENKINS_CONFIG.md).

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
2. Verify Docker socket permissions: The Jenkins container needs read/write access. The socket should be owned by `root:docker` with permissions `srw-rw----` (typically mode `0660`). Check with: `ls -l /var/run/docker.sock`
3. Ensure ports `8080` and `50000` are not in use

### Configuration not applied

1. Check JCasC logs in Jenkins: `Manage Jenkins` → `System Log` → `Configuration as Code`
2. Verify `jenkins.yaml` syntax is correct
3. Ensure the configuration file is mounted correctly

### Multi-arch build issues

1. Ensure Docker Buildx is installed: `docker buildx version`
2. Create a new builder: `docker buildx create --name multiarch --use`
3. Inspect builder: `docker buildx inspect --bootstrap`

## Tests

This repository includes comprehensive unit tests for the Jenkins configuration, covering:

- User authentication (admin and regular users)
- Admin permissions (Overall/Administer)
- User permissions (Job/Read, Job/Build, Job/Cancel, Job/Workspace, View/Read)
- Container health checks

For detailed information about running and maintaining the tests, see [TEST_README.md](TEST_README.md).

## Stopping Jenkins

```bash
docker-compose down
```

To remove volumes (⚠️ this deletes all Jenkins data):

```bash
docker-compose down -v
```

## License

See [LICENSE](LICENSE) file for details.
