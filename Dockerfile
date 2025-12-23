# Stage 1: Base image with system packages
FROM jenkins/jenkins:lts-jdk21 AS base

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
