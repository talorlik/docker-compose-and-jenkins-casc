# Jenkins Configuration as Code (JCasC) Documentation

> [INFO!] This document provides a detailed explanation of the `jenkins.yaml` configuration file used to configure Jenkins via Configuration as Code (JCasC).

## Table of Contents

- [Overview](#overview)
- [Top-Level Configuration](#top-level-configuration)
- [Security Configuration](#security-configuration)
- [Authorization Strategy](#authorization-strategy)
- [System Settings](#system-settings)
- [Node Configuration](#node-configuration)
- [Docker Cloud Configuration](#docker-cloud-configuration)
- [Unclassified Settings](#unclassified-settings)
- [Tool Installations](#tool-installations)

## Overview

The `jenkins.yaml` file uses YAML syntax to define Jenkins configuration declaratively. This allows you to version control your Jenkins setup and reproduce it consistently across environments.

## Top-Level Configuration

### `jenkins.systemMessage`

```yaml
systemMessage: "Jenkins configured automatically by Jenkins Configuration as Code"
```

**What it does**: Sets a system message that appears at the top of the Jenkins dashboard.

**Purpose**: Provides information to users about how Jenkins is configured. This message is visible to all users when they access the Jenkins web interface.

**Customization**: Change the message to reflect your organization's policies or setup information.

## Security Configuration

### `jenkins.securityRealm.local`

```yaml
securityRealm:
  local:
    allowsSignup: false
    users:
      - id: "admin"
        name: "Jenkins Admin"
        password: "${JENKINS_ADMIN_PASSWORD:-admin123}"
        properties: [...]
      - id: "user"
        name: "Jenkins User"
        password: "${JENKINS_USER_PASSWORD:-user123}"
        properties: [...]
```

**What it does**: Configures local user authentication for Jenkins.

**Key Components**:

- **`allowsSignup: false`**: Prevents users from creating their own accounts. Only users defined in this configuration can log in.
- **`users`**: Array of user accounts with the following properties:
  - **`id`**: The username used for login.
  - **`name`**: Display name shown in the UI.
  - **`password`**: User password (supports environment variable substitution).
    - `${JENKINS_ADMIN_PASSWORD:-admin123}` means: use `JENKINS_ADMIN_PASSWORD` if set, otherwise default to `admin123`.
  - **`properties`**: User properties that define additional capabilities and settings.

**User Properties Explained**:

- **`hudson.model.MyViewsProperty`**: Allows users to have custom views.
- **`hudson.security.HudsonPrivateSecurityRealm$Details`**: Stores user authentication details.
- **`jenkins.security.ApiTokenProperty`**: Enables API token generation for the user.
- **`hudson.model.PaneStatusProperties`**: Stores UI pane visibility preferences.
- **`jenkins.security.seed.UserSeedProperty`**: Used for secure random number generation.
- **`hudson.search.UserSearchProperty`**: Enables user search functionality.
- **`hudson.model.TimeZoneProperty`**: Allows users to set their timezone preference.

**Security Note**: Always use environment variables for passwords in production. Never commit plain-text passwords to version control.

## Authorization Strategy

### `jenkins.authorizationStrategy.globalMatrix`

```yaml
authorizationStrategy:
  globalMatrix:
    entries:
      - "Overall/Administer:admin"
      - "Overall/Read:authenticated"
      - "Job/Build:authenticated"
      - "Job/Cancel:authenticated"
      - "Job/Read:authenticated"
      - "Job/Workspace:authenticated"
      - "View/Read:authenticated"
      - "View/Read:user"
      - "Job/Read:user"
      - "Job/Build:user"
      - "Job/Cancel:user"
      - "Job/Workspace:user"
```

**What it does**: Defines fine-grained permissions for users and groups using a matrix-based authorization strategy.

**Permission Format**: `"Permission/Type:UserOrGroup"`

**Permission Types Explained**:

- **`Overall/Administer`**: Full administrative access to Jenkins (system configuration, user management, etc.).
- **`Overall/Read`**: Ability to view Jenkins (required for all authenticated users).
- **`Job/Build`**: Permission to trigger builds.
- **`Job/Cancel`**: Permission to cancel running builds.
- **`Job/Read`**: Permission to view job configurations and build history.
- **`Job/Workspace`**: Permission to access job workspace files.
- **`View/Read`**: Permission to view and access views.

**User/Groups**:

- **`admin`**: Specific user (the admin user).
- **`user`**: Specific user (the regular user).
- **`authenticated`**: All logged-in users.

**In This Configuration**:

- **Admin user** (`admin`): Has `Overall/Administer` - full access.
- **All authenticated users**: Can read, build, cancel jobs, and access workspaces.
- **Regular user** (`user`): Has explicit permissions for views and jobs (redundant but explicit).

**Alternative Strategies**: You could also use:

- `loggedInUsersCanDoAnything`: All logged-in users have admin access (not recommended for production).
- `roleStrategy`: Role-based access control (more complex but more flexible).

## System Settings

### `jenkins.crumbIssuer`

```yaml
crumbIssuer:
  standard:
    excludeClientIPFromCrumb: false
```

**What it does**: Configures CSRF (Cross-Site Request Forgery) protection.

**Components**:

- **`standard`**: Uses Jenkins' standard crumb issuer.
- **`excludeClientIPFromCrumb: false`**: Includes the client IP address in the CSRF token.

**Purpose**: Prevents CSRF attacks by requiring a token (crumb) for state-changing operations.

**Note**: Setting `excludeClientIPFromCrumb: true` can help with load balancers or proxies, but may reduce security.

### `jenkins.disableRememberMe`

```yaml
disableRememberMe: false
```

**What it does**: Controls whether users can use the "Remember Me" checkbox on the login page.

- **`false`**: Users can check "Remember Me" to stay logged in.
- **`true`**: "Remember Me" option is disabled.

### `jenkins.numExecutors`

```yaml
numExecutors: 2
```

**What it does**: Sets the number of concurrent builds that can run on the Jenkins master node.

**Purpose**: Controls resource usage. More executors = more parallel builds, but also more CPU/memory usage.

**Recommendation**: Typically set to the number of CPU cores, or slightly less to leave resources for the Jenkins process itself.

### `jenkins.mode`

```yaml
mode: NORMAL
```

**What it does**: Sets the Jenkins instance mode.

**Options**:

- **`NORMAL`**: Standard mode - Jenkins can run builds and manage agents.
- **`EXCLUSIVE`**: Jenkins only runs builds, no agent management.
- **`NORMAL`** is the standard choice for most setups.

## Node Configuration

### `jenkins.nodes`

```yaml
nodes:
  - permanent:
      name: "master"
      numExecutors: 2
      description: "Built-in Jenkins node"
      remoteFS: "/var/jenkins_home"
      labelString: "master"
      launcher:
        jnlp:
          workDirSettings:
            disabled: false
            failIfWorkDirIsMissing: false
            internalDir: "remoting"
            workDirPath: "/var/jenkins_home"
```

**What it does**: Configures the Jenkins master node (the built-in node).

**Components**:

- **`permanent`**: Defines a permanent node (as opposed to temporary/ephemeral).
- **`name: "master"`**: Node identifier.
- **`numExecutors: 2`**: Number of concurrent builds on this node.
- **`description`**: Human-readable description.
- **`remoteFS: "/var/jenkins_home"`**: Root filesystem path for the node.
- **`labelString: "master"`**: Labels that can be used to target this node in pipelines.
- **`launcher.jnlp`**: JNLP (Java Network Launch Protocol) launcher configuration.
  - **`workDirSettings`**: Working directory settings.
    - **`disabled: false`**: Work directory is enabled.
    - **`failIfWorkDirIsMissing: false`**: Don't fail if work directory doesn't exist.
    - **`internalDir: "remoting"`**: Internal directory name.
    - **`workDirPath: "/var/jenkins_home"`**: Path to the working directory.

**Purpose**: This configuration ensures the master node is properly set up and can execute builds.

## Docker Cloud Configuration

### `jenkins.nodes.clouds`

```yaml
nodes:
  - permanent:
      # ... node configuration ...
    clouds:
      - docker:
          name: "docker"
          dockerApi:
            dockerHost:
              uri: "unix:///var/run/docker.sock"
          containerCapStr: "10"
          templates:
            - labelString: "docker"
              name: "docker-agent"
              remoteFs: "/home/jenkins/agent"
              instanceCapStr: "5"
              mode: NORMAL
              pullStrategy: PULL_ALWAYS
              dockerTemplateBase:
                image: "jenkins/inbound-agent:latest"
                memoryLimit: 2048
                cpuPeriod: 100000
                cpuQuota: 100000
                volumes:
                  - "/var/run/docker.sock:/var/run/docker.sock"
```

**What it does**: Configures Docker Cloud, which allows Jenkins to dynamically provision Docker containers as build agents.

**Components**:

- **`name: "docker"`**: Identifier for this cloud configuration.
- **`dockerApi.dockerHost.uri`**: Docker daemon connection URI.
  - **`unix:///var/run/docker.sock`**: Connects to Docker daemon via Unix socket (standard on Linux).
- **`containerCapStr: "10"`**: Maximum total number of containers that can be created across all templates (as a string).
- **`templates`**: Defines agent container templates.
  - **`labelString: "docker"`**: Label that pipelines can use to request this agent type.
  - **`name: "docker-agent"`**: Template name.
  - **`remoteFs: "/home/jenkins/agent"`**: Root filesystem path inside the container.
  - **`instanceCapStr: "5"`**: Maximum number of containers of this template that can run simultaneously (as a string).
  - **`mode: NORMAL`**: Agent mode (NORMAL allows running builds).
  - **`pullStrategy: PULL_ALWAYS`**: Always pull the latest image (options: `PULL_ALWAYS`, `PULL_NEVER`, `PULL_LATEST`).
  - **`dockerTemplateBase`**: Base configuration for Docker agent containers.
    - **`image: "jenkins/inbound-agent:latest"`**: Docker image to use for agents.
    - **`memoryLimit: 2048`**: Memory limit per agent container in megabytes (2048 MB = 2 GB).
    - **`cpuPeriod: 100000`**: CPU period in microseconds (used with cpuQuota for CPU limits).
    - **`cpuQuota: 100000`**: CPU quota in microseconds (100000/100000 = 1.0 CPU core per agent).
    - **`volumes`**: Volumes to mount in agent containers.
      - Mounts Docker socket so agents can build Docker images (Docker-in-Docker).

**Resource Limits Explained**:

- **Memory**: Each agent container is limited to 2048 MB (2 GB) of RAM. This prevents agents from consuming excessive memory.
- **CPU**: Each agent container is limited to 1 CPU core (cpuQuota/cpuPeriod = 100000/100000 = 1.0).
  - **`cpuPeriod`**: The period over which CPU usage is measured (100000 microseconds = 0.1 seconds).
  - **`cpuQuota`**: The maximum CPU time allowed in one period (100000 microseconds = 1 full CPU core).
  - To set 0.5 CPU: `cpuQuota: 50000` (50% of one core).
  - To set 2 CPUs: `cpuQuota: 200000` (2 full cores).

**Purpose**: Resource limits ensure that:

- Agent containers don't consume all available system resources.
- Multiple agents can run simultaneously without resource contention.
- System resources are predictable and manageable.

**How It Works**: When a pipeline requests an agent with `label 'docker'`, Jenkins creates a container from the specified image, runs the build, then removes the container.

**Use Case**: Provides isolated, clean build environments for each job execution.

## Unclassified Settings

### `unclassified.location`

```yaml
unclassified:
  location:
    adminAddress: "${JENKINS_ADMIN_EMAIL:-admin@example.com}"
    url: "http://localhost:8080/"
```

**What it does**: Sets Jenkins system location settings.

**Components**:

- **`adminAddress`**: Email address of the Jenkins administrator (can be set via the `JENKINS_ADMIN_EMAIL` environment variable; defaults to `admin@example.com` if not specified, as in the `jenkins.yaml`).
- **`url`**: Public URL of the Jenkins instance (used in links and notifications).

**Purpose**: These settings are used in email notifications, build links, and other system-generated content.

**Important**: Update the `url` to match your actual Jenkins URL (e.g., `https://jenkins.example.com`).

### `unclassified.globalLibraries`

```yaml
globalLibraries:
  libraries:
    - name: "shared-library"
      defaultVersion: "master"
      retriever:
        modernSCM:
          scm:
            git:
              id: "shared-library"
              remote: "https://github.com/jenkinsci/workflow-cps-global-lib-plugin.git"
```

**What it does**: Configures global shared libraries for Jenkins pipelines.

**Components**:

- **`name: "shared-library"`**: Library identifier.
- **`defaultVersion: "master"`**: Git branch/tag to use by default.
- **`retriever.modernSCM.scm.git`**: Git SCM configuration.
  - **`id`**: Unique identifier.
  - **`remote`**: Git repository URL.

**Purpose**: Shared libraries allow you to define reusable pipeline code that can be imported into any Jenkinsfile.

**Usage in Pipeline**:

```groovy
@Library('shared-library') _
```

**Note**: The example uses a demo repository. Replace with your own shared library repository.

## Tool Installations

### `tool.git`

```yaml
tool:
  git:
    installations:
      - name: "Default"
        home: "git"
```

**What it does**: Configures Git installation for Jenkins.

**Components**:

- **`name: "Default"`**: Installation name (used in pipelines).
- **`home: "git"`**: Path to Git executable or "git" to use system PATH.

**Purpose**: Allows Jenkins to use Git for source control operations.

**Usage**: Jenkins will automatically find Git using this configuration when checking out repositories.

### `tool.docker`

```yaml
docker:
  installations:
    - name: "Docker"
      home: "/usr/bin/docker"
```

**What it does**: Configures Docker installation for Jenkins.

**Components**:

- **`name: "Docker"`**: Installation name (used in pipelines).
- **`home: "/usr/bin/docker"`**: Path to Docker executable.

**Purpose**: Allows Jenkins pipelines to use Docker commands (build images, run containers, etc.).

**Note**: This path should match where Docker CLI is installed in your Jenkins container (see Dockerfile).

## Environment Variables

The configuration uses environment variables for sensitive values:

- **`${JENKINS_ADMIN_PASSWORD:-admin123}`**: Admin user password.
- **`${JENKINS_USER_PASSWORD:-user123}`**: Regular user password.

**Syntax**: `${VARIABLE_NAME:-default_value}` means "use VARIABLE_NAME if set, otherwise use default_value"

**Set in**: `docker-compose.yaml` or `.env` file

## Best Practices

1. **Never commit passwords**: Always use environment variables for sensitive data.
2. **Version control**: Keep `jenkins.yaml` in version control for reproducibility.
3. **Test changes**: Test configuration changes in a development environment first.
4. **Document customizations**: Add comments for non-standard configurations.
5. **Regular updates**: Review and update configurations as Jenkins and plugins evolve.

## Additional Resources

- [Jenkins Configuration as Code Plugin Documentation](https://github.com/jenkinsci/configuration-as-code-plugin)
- [JCasC Schema Reference](https://github.com/jenkinsci/configuration-as-code-plugin/blob/master/docs/SCHEMAS.md)
- [Jenkins Pipeline Documentation](https://www.jenkins.io/doc/book/pipeline/)
