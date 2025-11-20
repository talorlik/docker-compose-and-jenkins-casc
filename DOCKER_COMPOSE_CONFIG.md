# Docker Compose Configuration Documentation

> [!INFO]
> This document provides a detailed explanation of the `docker-compose.yaml` configuration file used to orchestrate the Jenkins container and its dependencies.

## Table of Contents

- [Overview](#overview)
- [Version Declaration](#version-declaration)
- [Services Configuration](#services-configuration)
- [Volumes Configuration](#volumes-configuration)
- [Networks Configuration](#networks-configuration)
- [Managing Environment Variables](#managing-environment-variables)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

Docker Compose is a tool for defining and running multi-container Docker applications. The `docker-compose.yaml` file uses YAML syntax to configure services, networks, and volumes in a declarative way.

This configuration defines a single Jenkins service with persistent storage, network isolation, and proper volume mounts for configuration and data persistence.

## Version Declaration

> [!NOTE]
> The `version` field has been removed as it's obsolete in Docker Compose v2 (the current standard). Docker Compose v2 automatically detects the file format and supports all modern features including:
>
> - Named volumes
> - Networks
> - Build configurations
> - Environment variable substitution
> - Health checks
> - Deploy configurations
> - Resource limits
> - Logging configuration

## Services Configuration

### `services.jenkins`

The `jenkins` service is the main container that runs the Jenkins server.

#### Build Configuration

```yaml
build:
  context: .
  dockerfile: Dockerfile
```

**What it does**: Tells Docker Compose to build the image from a Dockerfile instead of using a pre-built image.

**Components**:

- **`context: .`**: The build context (current directory). All files in this directory are available during the build.
- **`dockerfile: Dockerfile`**: Specifies which Dockerfile to use (defaults to `Dockerfile` in the context).

**Purpose**: Builds a custom Jenkins image with pre-installed plugins and Docker CLI.

**Alternative**: You could use `image: jenkins/jenkins:latest-jdk21` to use a pre-built image, but then plugins wouldn't be pre-installed.

#### Container Name

```yaml
container_name: jenkins
```

**What it does**: Sets a custom name for the container instead of the auto-generated name.

**Purpose**: Makes it easier to reference the container in commands:

- `docker ps` shows "jenkins" instead of "docker-compose-and-jenkins-casc_jenkins_1".
- `docker logs jenkins` works directly.
- `docker exec -it jenkins bash` is simpler.

**Note**: If you scale the service (run multiple instances), you cannot use `container_name` as each container needs a unique name.

#### User Configuration

```yaml
user: root
```

**What it does**: Runs the container as the root user.

**Purpose**: Required for Docker-in-Docker functionality. The container needs root access to:

- Access the Docker socket (`/var/run/docker.sock`).
- Execute Docker commands.
- Manage Docker containers.

**Security Note**: Running as root is a security consideration. In production, consider:

- Using Docker-in-Docker (DinD) containers.
- Using a separate Docker daemon.
- Using rootless Docker.
- Implementing proper access controls.

#### Port Mapping

```yaml
ports:
  - "8080:8080"
  - "50000:50000"
```

**What it does**: Maps container ports to host ports.

**Format**: `"HOST_PORT:CONTAINER_PORT"`

**Ports Explained**:

- **`8080:8080`**: Jenkins web interface.
  - Host port 8080 → Container port 8080.
  - Access Jenkins at `http://localhost:8080`.
  - Change the host port (e.g., `"9080:8080"`) if 8080 is already in use.

- **`50000:50000`**: Jenkins agent communication port.
  - Used for JNLP (Java Network Launch Protocol) agents.
  - Required for agent connections.
  - Change if you have port conflicts.

**Alternative Syntax**: You can also use:

- `"8080:8080/tcp"` to explicitly specify TCP (default).
- `"8080:8080/udp"` for UDP.
- `"127.0.0.1:8080:8080"` to bind to a specific host interface.

#### Volume Mounts

```yaml
volumes:
  - jenkins_home:/var/jenkins_home
  - ./jenkins.yaml:/var/jenkins_home/casc_configs/jenkins.yaml:ro
  - /var/run/docker.sock:/var/run/docker.sock
```

**What it does**: Mounts directories/files from the host or named volumes into the container.

**Volume Types**:

1. **Named Volume**:

   ```yaml
   jenkins_home:/var/jenkins_home
   ```

   - **`jenkins_home`**: Named volume (defined in `volumes` section)
   - **`/var/jenkins_home`**: Mount point inside container
   - **Purpose**: Persistent storage for Jenkins data, configurations, plugins, and build history
   - **Location**: Managed by Docker (typically in `/var/lib/docker/volumes/`)

2. **Bind Mount (Read-Only)**:

   ```yaml
   ./jenkins.yaml:/var/jenkins_home/casc_configs/jenkins.yaml:ro
   ```

   - **`./jenkins.yaml`**: Host file (relative to docker-compose.yaml location)
   - **`/var/jenkins_home/casc_configs/jenkins.yaml`**: Container path
   - **`:ro`**: Read-only mount (container cannot modify the file)
   - **Purpose**: Provides JCasC configuration file to Jenkins
   - **Why Read-Only**: Prevents accidental modification from inside the container

3. **Bind Mount (Docker Socket)**:

   ```yaml
   /var/run/docker.sock:/var/run/docker.sock
   ```

   - **`/var/run/docker.sock`**: Host Docker daemon socket
   - **Same path in container**: Mounts to the same location
   - **Purpose**: Allows Jenkins to communicate with the host's Docker daemon
   - **Use Case**: Enables Docker-in-Docker functionality (building images, running containers from pipelines)
   - **Security Note**: This gives the container full access to the Docker daemon

**Volume Options**:

- **`:ro`**: Read-only mount
- **`:rw`**: Read-write mount (default)
- **`:z`**: SELinux shared content label
- **`:Z`**: SELinux private unshared label

#### Environment Variables

```yaml
environment:
  - JENKINS_OPTS=--httpPort=8080
  - CASC_JENKINS_CONFIG=/var/jenkins_home/casc_configs
  - JENKINS_ADMIN_PASSWORD=${JENKINS_ADMIN_PASSWORD:-admin123}
  - JENKINS_USER_PASSWORD=${JENKINS_USER_PASSWORD:-user123}
```

**What it does**: Sets environment variables inside the container.

**Variables Explained**:

1. **`JENKINS_OPTS=--httpPort=8080`**:
   - Jenkins startup options.
   - `--httpPort=8080` sets the HTTP port (matches the port mapping).
   - Additional options can be added: `--prefix=/jenkins`, `--httpsPort=8443`, etc.

2. **`CASC_JENKINS_CONFIG=/var/jenkins_home/casc_configs`**:
   - Tells the Configuration as Code plugin where to find configuration files.
   - Points to the directory where `jenkins.yaml` is mounted.
   - JCasC plugin scans this directory for `.yaml` and `.yml` files.

3. **`JENKINS_ADMIN_PASSWORD=${JENKINS_ADMIN_PASSWORD:-admin123}`**:
   - Admin user password (used in `jenkins.yaml`).
   - **Syntax**: `${VARIABLE:-default}` means "use VARIABLE if set, otherwise use default".
   - Can be set in `.env` file or shell environment.
   - Default: `admin123`.

4. **`JENKINS_USER_PASSWORD=${JENKINS_USER_PASSWORD:-user123}`**:
   - Regular user password (used in `jenkins.yaml`)
   - Same syntax as admin password
   - Default: `user123`

**Setting Environment Variables**:

1. **`.env` file** (recommended):

   ```bash
   JENKINS_ADMIN_PASSWORD=my-secure-password
   JENKINS_USER_PASSWORD=another-secure-password
   ```

2. **Shell environment**:

   ```bash
   export JENKINS_ADMIN_PASSWORD=my-secure-password
   docker compose up -d
   ```

3. **Direct in docker-compose.yaml** (not recommended for secrets):

   ```yaml
   - JENKINS_ADMIN_PASSWORD=my-password
   ```

#### Restart Policy

```yaml
restart: unless-stopped
```

**What it does**: Configures when Docker should automatically restart the container.

**Options**:

- **`no`**: Never restart (default).
- **`always`**: Always restart, even if manually stopped.
- **`on-failure`**: Restart only on failure (non-zero exit code).
- **`unless-stopped`**: Restart always, except when manually stopped.

**Purpose**: Ensures Jenkins automatically restarts after:

- System reboot.
- Docker daemon restart.
- Container crash.

**Why `unless-stopped`**: Allows you to manually stop the container (`docker-compose stop`) without it automatically restarting, but will restart on system reboots.

#### Resource Limits

```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 4G
    reservations:
      cpus: '1'
      memory: 2G
```

**What it does**: Sets CPU and memory limits and reservations for the Jenkins container.

**Components**:

- **`limits`**: Maximum resources the container can use.
  - **`cpus: '2'`**: Maximum of 2 CPU cores.
  - **`memory: 4G`**: Maximum of 4 gigabytes of RAM.
- **`reservations`**: Guaranteed minimum resources allocated to the container.
  - **`cpus: '1'`**: Guaranteed 1 CPU core.
  - **`memory: 2G`**: Guaranteed 2 gigabytes of RAM.

**Purpose**: Prevents the container from consuming excessive system resources and ensures it has minimum resources available.

**Benefits**:

- **Resource protection**: Prevents Jenkins from starving other services.
- **Predictable performance**: Guaranteed minimum resources ensure consistent operation.
- **Resource planning**: Helps with capacity planning and resource allocation.

**Adjusting Limits**: Modify these values based on your workload:

- Light usage: `cpus: '1'`, `memory: 2G`.
- Medium usage: `cpus: '2'`, `memory: 4G` (current setting).
- Heavy usage: `cpus: '4'`, `memory: 8G` or more.

#### Health Check

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8080/login"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 60s
```

**What it does**: Configures a health check to monitor Jenkins container health.

**Components**:

- **`test`**: Command to check container health.
  - **`CMD`**: Execute command inside the container.
  - **`curl -f http://localhost:8080/login`**: Checks if Jenkins login page is accessible (returns non-zero on failure).
- **`interval: 30s`**: Time between health checks (30 seconds).
- **`timeout: 10s`**: Maximum time to wait for health check to complete.
- **`retries: 3`**: Number of consecutive failures before marking as unhealthy.
- **`start_period: 60s`**: Grace period during container startup (60 seconds) where failures don't count.

**Purpose**: Enables Docker and orchestration tools to detect when Jenkins is unhealthy and take action (restart, remove from load balancer, etc.).

**Health Status**:

- **Healthy**: Container is responding correctly.
- **Unhealthy**: Container failed health checks (after retries).
- **Starting**: Container is in start_period grace period.

**Monitoring**: Check container health with:

```bash
docker ps  # Shows health status
docker inspect jenkins | grep -A 10 Health
```

**Note**: Requires `curl` to be installed in the container (included in the Dockerfile).

#### Logging Configuration

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

**What it does**: Configures log rotation to prevent log files from growing unbounded.

**Components**:

- **`driver: "json-file"`**: Uses JSON file logging driver (default, structured logs).
- **`max-size: "10m"`**: Maximum size per log file (10 megabytes).
- **`max-file: "3"`**: Maximum number of log files to keep (3 files).

**Purpose**: Prevents log files from consuming excessive disk space.

**How It Works**:

1. When a log file reaches 10MB, it's rotated.
2. Old logs are kept in numbered files (e.g., `jenkins-json.log.1`, `jenkins-json.log.2`).
3. Only the 3 most recent log files are kept (30MB total maximum).
4. Older logs are automatically deleted.

**Benefits**:

- **Disk space management**: Prevents logs from filling up disk.
- **Log retention**: Keeps recent logs for troubleshooting.
- **Performance**: Smaller log files are easier to read and process.

**Viewing Logs**:

```bash
docker compose logs jenkins        # View all logs
docker compose logs -f jenkins     # Follow logs in real-time
docker compose logs --tail=100 jenkins  # Last 100 lines
```

**Alternative Drivers**: You can also use:

- `syslog`: Send logs to syslog.
- `journald`: Send logs to systemd journal (Linux).
- `gelf`: Send logs to Graylog or Logstash.
- `fluentd`: Send logs to Fluentd.

#### Network Configuration

```yaml
networks:
  - jenkins-network
```

**What it does**: Connects the service to a custom network.

**Purpose**:

- Isolates Jenkins from other Docker containers.
- Allows multiple services to communicate on the same network.
- Provides DNS resolution between services.

**Benefits**: If you add more services (database, reverse proxy, etc.), they can communicate using service names as hostnames.

## Volumes Configuration

```yaml
volumes:
  jenkins_home:
    driver: local
```

**What it does**: Defines named volumes for data persistence.

**Components**:

- **`jenkins_home`**: Volume name (referenced in service volumes).
- **`driver: local`**: Storage driver (stores data on local filesystem).

**Purpose**: Creates a persistent volume that survives container removal.

**Volume Location**:

- Linux: `/var/lib/docker/volumes/jenkins_home/_data`.
- Docker Desktop (Mac/Windows): Inside the Docker VM.

**Data Persistence**:

- Jenkins configurations
- Installed plugins
- Build history
- Job configurations
- User data

**Managing Volumes**:

- **List volumes**: `docker volume ls`.
- **Inspect volume**: `docker volume inspect jenkins_home`.
- **Remove volume**: `docker volume rm jenkins_home` (⚠️ deletes all data).
- **Backup volume**: Copy data from volume location or use backup tools.

**Alternative Drivers**:

- `driver: nfs` - Network File System.
- `driver: cifs` - Windows shares.
- `driver: tmpfs` - Temporary filesystem (data lost on restart).

## Networks Configuration

```yaml
networks:
  jenkins-network:
    driver: bridge
```

**What it does**: Defines a custom Docker network.

**Components**:

- **`jenkins-network`**: Network name (referenced in service networks).
- **`driver: bridge`**: Network driver (default, creates isolated network).

**Purpose**: Creates an isolated network for Jenkins and related services.

**Network Types**:

- **`bridge`**: Default driver, creates isolated network on single host.
- **`host`**: Uses host's network directly (no isolation).
- **`overlay`**: For multi-host networking (Docker Swarm).
- **`macvlan`**: Assigns MAC address to container (appears as physical device).

**Benefits of Custom Network**:

- Service discovery (containers can reach each other by name).
- Network isolation from other Docker networks.
- Custom DNS resolution.
- Better security (only services on this network can communicate).

**Network Commands**:

- **List networks**: `docker network ls`.
- **Inspect network**: `docker network inspect jenkins-network`.
- **Remove network**: `docker network rm jenkins-network`.

## Managing Environment Variables

### Setting Passwords

Create a `.env` file in the same directory as `docker-compose.yaml`:

```bash
JENKINS_ADMIN_PASSWORD=your-secure-admin-password
JENKINS_USER_PASSWORD=your-secure-user-password
```

**Security Best Practices**:

1. **Never commit `.env` files** to version control (already in `.gitignore`).
2. **Use strong passwords** in production.
3. **Rotate passwords** regularly.
4. **Use secrets management** (Docker Secrets, HashiCorp Vault, etc.) for production.

### Available Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `JENKINS_ADMIN_PASSWORD` | `admin123` | Admin user password |
| `JENKINS_USER_PASSWORD` | `user123` | Regular user password |

## Best Practices

1. **Use `.env` file for secrets**: Never hardcode passwords in `docker-compose.yaml`.
2. **Version control**: Commit `docker-compose.yaml` but not `.env` files.
3. **Named volumes**: Use named volumes for data that should persist.
4. **Read-only mounts**: Mount configuration files as read-only when possible.
5. **Resource limits**: ✅ **Implemented** - Resource limits are configured in the `deploy.resources` section (see [Resource Limits](#resource-limits) above).

6. **Health checks**: ✅ **Implemented** - Health check is configured to monitor Jenkins availability (see [Health Check](#health-check) above).

7. **Logging**: ✅ **Implemented** - Log rotation is configured to prevent log files from growing unbounded (see [Logging Configuration](#logging-configuration) above).

## Troubleshooting

### Container won't start

1. **Check logs**: `docker-compose logs jenkins`.
2. **Verify ports**: Ensure ports 8080 and 50000 are not in use.
3. **Check Docker socket**: Verify `/var/run/docker.sock` exists and has correct permissions.
4. **Check volumes**: Ensure volume paths are correct.

### Configuration not applied

1. **Verify mount**: Check that `jenkins.yaml` is mounted correctly.
2. **Check path**: Ensure `CASC_JENKINS_CONFIG` points to the correct directory.
3. **Check permissions**: Verify file permissions on `jenkins.yaml`.
4. **Check logs**: Look for JCasC errors in Jenkins logs.

### Docker socket permission denied

1. **Check ownership**: `ls -l /var/run/docker.sock`.
2. **Add user to docker group**: `sudo usermod -aG docker $USER` (Linux).
3. **Restart Docker**: `sudo systemctl restart docker` (Linux).
4. **On Mac/Windows**: Docker Desktop handles this automatically.

### Volume data lost

1. **Check volume exists**: `docker volume ls`.
2. **Verify volume mount**: Check `docker-compose.yaml` volume configuration.
3. **Check volume location**: `docker volume inspect jenkins_home`.
4. **Backup before changes**: Always backup volumes before major changes.

### Port conflicts

1. **Change host port**: Modify `"8080:8080"` to `"9080:8080"` (or any available port).
2. **Check what's using port**:
   - Linux: `sudo lsof -i :8080`.
   - Mac: `lsof -i :8080`.
   - Windows: `netstat -ano | findstr :8080`.

## Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Docker Compose File Reference](https://docs.docker.com/compose/compose-file/)
- [Docker Volumes Documentation](https://docs.docker.com/storage/volumes/)
- [Docker Networks Documentation](https://docs.docker.com/network/)
