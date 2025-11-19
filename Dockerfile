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

USER jenkins
