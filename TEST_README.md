# Jenkins Configuration Tests

This directory contains unit tests for the Jenkins Configuration as Code setup.

## Test Coverage

The test suite covers the following scenarios:

1. **Authentication Tests** (`TestJenkinsAuthentication`)
   - Admin user can successfully log in with the configured password.
   - DevOps user can successfully log in with the configured password.
   - Login fails with incorrect passwords.

2. **Admin Permissions Tests** (`TestAdminPermissions`)
   - Admin user has `Overall/Administer` permission.
   - Admin can access Manage Jenkins page.
   - Admin can access Configuration as Code page.
   - Admin can reload Jenkins configuration.

3. **DevOps Permissions Tests** (`TestDevOpsPermissions`)
   - DevOps user cannot access administrative pages.
   - DevOps user has `Job/Read` permission.
   - DevOps user has `Job/Build` permission.
   - DevOps user has `Job/Cancel` permission.
   - DevOps user has `Job/Workspace` permission.
   - DevOps user has `View/Read` permission.

4. **Container Health Check Tests** (`TestContainerHealthCheck`)
   - Jenkins container reports healthy status via Docker health check.
   - Health check endpoint (`/login`) is accessible.
   - Jenkins web interface is accessible.

## Prerequisites

1. **Jenkins Running**: The tests require Jenkins to be running. Start it with:

   ```bash
   docker compose up -d --build
   ```

2. **Python 3.7+**: Tests are written in Python using pytest.

3. **Test Dependencies**: Install the required Python packages:

   ```bash
   pip install -r requirements-test.txt
   ```

## Running the Tests

### Run All Tests

```bash
pytest test_jenkins.py -v
```

### Run Specific Test Classes

```bash
# Run only authentication tests
pytest test_jenkins.py::TestJenkinsAuthentication -v

# Run only admin permission tests
pytest test_jenkins.py::TestAdminPermissions -v

# Run only devops permission tests
pytest test_jenkins.py::TestDevOpsPermissions -v

# Run only health check tests
pytest test_jenkins.py::TestContainerHealthCheck -v
```

### Run Specific Test Cases

```bash
# Test admin login
pytest test_jenkins.py::TestJenkinsAuthentication::test_admin_login_success -v

# Test devops permissions
pytest test_jenkins.py::TestDevOpsPermissions::test_devops_has_job_read_permission -v

# Test health check
pytest test_jenkins.py::TestContainerHealthCheck::test_health_check_reports_healthy_status -v
```

## Configuration

The tests can be configured using environment variables:

- `JENKINS_URL`: Jenkins server URL (default: `http://localhost:8080`).
- `JENKINS_ADMIN_PASSWORD`: Admin password (default: `admin123`).
- `JENKINS_DEVOPS_PASSWORD`: DevOps user password (default: `devops123`).

**Note**: In production, passwords are loaded from Docker Compose secrets. For testing, you can set these environment variables or use the defaults.

### Example with Custom Configuration

```bash
# Test against a different Jenkins instance
JENKINS_URL=http://jenkins.example.com:8080 pytest test_jenkins.py -v

# Test with custom passwords (from secrets)
JENKINS_ADMIN_PASSWORD=$(cat secrets/jenkins_admin_password) \
JENKINS_DEVOPS_PASSWORD=$(cat secrets/jenkins_devops_password) \
pytest test_jenkins.py -v
```

## Test Output

The tests use pytest's verbose mode (`-v`) to provide detailed output:

```bash
test_jenkins.py::TestJenkinsAuthentication::test_admin_login_success PASSED
test_jenkins.py::TestJenkinsAuthentication::test_devops_login_success PASSED
test_jenkins.py::TestAdminPermissions::test_admin_has_overall_administer_permission PASSED
test_jenkins.py::TestDevOpsPermissions::test_devops_has_job_read_permission PASSED
test_jenkins.py::TestContainerHealthCheck::test_health_check_reports_healthy_status PASSED
```

## Troubleshooting

### Jenkins Not Ready

If tests fail because Jenkins is not ready:

- The tests automatically wait up to 120 seconds for Jenkins to start.
- Increase `JENKINS_STARTUP_TIMEOUT` in `test_jenkins.py` if needed.
- Check Jenkins logs: `docker compose logs jenkins`.

### Connection Refused

If you get connection errors:

- Ensure Jenkins is running: `docker ps | grep jenkins`.
- Verify Jenkins is accessible: `curl http://localhost:8080/login`.
- Check that port 8080 is not blocked by a firewall.

### Health Check Test Fails

If the health check test fails:

- Ensure Docker is installed and accessible.
- Check container status: `docker ps --filter name=jenkins`.
- Verify the health check is configured in `docker-compose.yaml`.

### Permission Tests Fail

If permission tests fail unexpectedly:

- Verify `jenkins.yaml` configuration is correct.
- Check that JCasC has applied the configuration: Visit Jenkins → Manage Jenkins → Configuration as Code.
- Review Jenkins logs for JCasC errors.

## CI/CD Integration

To integrate these tests into a CI/CD pipeline:

```bash
#!/bin/bash
# Start Jenkins
docker compose up -d --build

# Wait for Jenkins to be ready and run tests
pytest test_jenkins.py -v --tb=short

# Store test results
TEST_RESULT=$?

# Cleanup (optional)
# docker compose down -v

# Exit with test result
exit $TEST_RESULT
```

## Test Maintenance

When updating `jenkins.yaml`:

- Review and update permission tests if authorization changes.
- Add new test cases for new users or permission configurations.
- Ensure tests reflect the current security model.
- Update environment variable names if password variables change (e.g., `JENKINS_DEVOPS_PASSWORD`).

## Additional Notes

- Tests create and delete temporary jobs for permission testing.
- All test jobs are prefixed with `test-job-*`.
- Tests use Jenkins REST API for validation.
- Tests respect CSRF protection (crumb issuer).
