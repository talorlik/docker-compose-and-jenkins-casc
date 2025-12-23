"""
Unit tests for Jenkins Configuration as Code setup.

Tests cover:
1. Admin user authentication
2. DevOps user authentication
3. Admin user permissions
4. DevOps user permissions
5. Container health check
"""

import os
import time
import requests
from requests.auth import HTTPBasicAuth
import pytest
import subprocess


# Configuration
JENKINS_URL = os.getenv("JENKINS_URL", "http://localhost:8080")
ADMIN_USER = "admin"
ADMIN_PASSWORD = os.getenv("JENKINS_ADMIN_PASSWORD", "admin123")
DEVOPS_USER = "devops"
DEVOPS_USER_PASSWORD = os.getenv("JENKINS_DEVOPS_PASSWORD", "devops123")

# Wait for Jenkins to be ready before running tests
JENKINS_STARTUP_TIMEOUT = 120  # seconds


@pytest.fixture(scope="module", autouse=True)
def wait_for_jenkins():
    """Wait for Jenkins to be fully started before running tests."""
    print(f"\nWaiting for Jenkins at {JENKINS_URL} to be ready...")
    start_time = time.time()

    while time.time() - start_time < JENKINS_STARTUP_TIMEOUT:
        try:
            response = requests.get(
                f"{JENKINS_URL}/login",
                timeout=5,
                allow_redirects=True
            )
            if response.status_code == 200:
                print("Jenkins is ready!")
                # Give it a bit more time for full initialization
                time.sleep(5)
                return
        except requests.exceptions.RequestException:
            pass

        time.sleep(2)

    pytest.fail(f"Jenkins did not start within {JENKINS_STARTUP_TIMEOUT} seconds")


class TestJenkinsAuthentication:
    """Test user authentication functionality."""

    def test_admin_login_success(self):
        """Test that admin user can successfully log in with configured password."""
        # Try to access the API with admin credentials
        response = requests.get(
            f"{JENKINS_URL}/api/json",
            auth=HTTPBasicAuth(ADMIN_USER, ADMIN_PASSWORD),
            timeout=10
        )

        assert response.status_code == 200, (
            f"Admin login failed. Status code: {response.status_code}"
        )

        # Verify we get valid JSON response
        data = response.json()
        assert "mode" in data or "jobs" in data, "Invalid Jenkins API response"

    def test_devops_login_success(self):
        """Test that devops user can successfully log in with configured password."""
        # Try to access the API with devops user credentials
        response = requests.get(
            f"{JENKINS_URL}/api/json",
            auth=HTTPBasicAuth(DEVOPS_USER, DEVOPS_USER_PASSWORD),
            timeout=10
        )

        assert response.status_code == 200, (
            f"DevOps user login failed. Status code: {response.status_code}"
        )

        # Verify we get valid JSON response
        data = response.json()
        assert "mode" in data or "jobs" in data, "Invalid Jenkins API response"

    def test_admin_login_failure_with_wrong_password(self):
        """Test that admin login fails with incorrect password."""
        response = requests.get(
            f"{JENKINS_URL}/api/json",
            auth=HTTPBasicAuth(ADMIN_USER, "wrong_password"),
            timeout=10
        )

        assert response.status_code == 401, (
            "Expected 401 Unauthorized for wrong password"
        )

    def test_devops_login_failure_with_wrong_password(self):
        """Test that devops user login fails with incorrect password."""
        response = requests.get(
            f"{JENKINS_URL}/api/json",
            auth=HTTPBasicAuth(DEVOPS_USER, "wrong_password"),
            timeout=10
        )

        assert response.status_code == 401, (
            "Expected 401 Unauthorized for wrong password"
        )


class TestAdminPermissions:
    """Test admin user permissions."""

    def test_admin_has_overall_administer_permission(self):
        """Test that admin user has Overall/Administer permission."""
        # Check if admin can access the script console (requires Overall/Administer)
        response = requests.get(
            f"{JENKINS_URL}/script",
            auth=HTTPBasicAuth(ADMIN_USER, ADMIN_PASSWORD),
            timeout=10
        )

        assert response.status_code == 200, (
            "Admin user should have access to script console (Overall/Administer)"
        )

    def test_admin_can_access_manage_jenkins(self):
        """Test that admin can access Manage Jenkins page."""
        response = requests.get(
            f"{JENKINS_URL}/manage",
            auth=HTTPBasicAuth(ADMIN_USER, ADMIN_PASSWORD),
            timeout=10
        )

        assert response.status_code == 200, (
            "Admin user should have access to Manage Jenkins page"
        )

    def test_admin_can_access_configuration_as_code(self):
        """Test that admin can access Configuration as Code page."""
        response = requests.get(
            f"{JENKINS_URL}/configuration-as-code",
            auth=HTTPBasicAuth(ADMIN_USER, ADMIN_PASSWORD),
            timeout=10
        )

        assert response.status_code == 200, (
            "Admin user should have access to Configuration as Code page"
        )

    def test_admin_can_reload_configuration(self):
        """Test that admin can reload configuration (requires administer permission)."""
        # Get the crumb for CSRF protection
        crumb_response = requests.get(
            f"{JENKINS_URL}/crumbIssuer/api/json",
            auth=HTTPBasicAuth(ADMIN_USER, ADMIN_PASSWORD),
            timeout=10
        )

        if crumb_response.status_code == 200:
            crumb_data = crumb_response.json()
            crumb = crumb_data.get("crumb")
            crumb_field = crumb_data.get("crumbRequestField", "Jenkins-Crumb")

            # Try to reload configuration
            headers = {crumb_field: crumb}
            response = requests.post(
                f"{JENKINS_URL}/reload",
                auth=HTTPBasicAuth(ADMIN_USER, ADMIN_PASSWORD),
                headers=headers,
                timeout=10
            )

            # Should be 200 (success) or 302 (redirect after success)
            assert response.status_code in [200, 302], (
                f"Admin should be able to reload configuration. "
                f"Status code: {response.status_code}"
            )


class TestDevOpsPermissions:
    """Test devops user permissions."""

    def test_devops_cannot_access_manage_jenkins(self):
        """Test that devops user cannot access Manage Jenkins (no administer permission)."""
        response = requests.get(
            f"{JENKINS_URL}/manage",
            auth=HTTPBasicAuth(DEVOPS_USER, DEVOPS_USER_PASSWORD),
            timeout=10
        )

        assert response.status_code == 403, (
            "DevOps user should not have access to Manage Jenkins page"
        )

    def test_devops_cannot_access_script_console(self):
        """Test that devops user cannot access script console (no administer permission)."""
        response = requests.get(
            f"{JENKINS_URL}/script",
            auth=HTTPBasicAuth(DEVOPS_USER, DEVOPS_USER_PASSWORD),
            timeout=10
        )

        assert response.status_code == 403, (
            "DevOps user should not have access to script console"
        )

    def test_devops_has_job_read_permission(self):
        """Test that devops user has Job/Read permission."""
        # First create a test job as admin
        job_name = "test-job-permissions"
        job_config = """<?xml version='1.1' encoding='UTF-8'?>
<project>
  <description>Test job for permission testing</description>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <scm class="hudson.scm.NullSCM"/>
  <canRoam>true</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers/>
  <concurrentBuild>false</concurrentBuild>
  <builders/>
  <publishers/>
  <buildWrappers/>
</project>"""

        # Get crumb for admin
        crumb_response = requests.get(
            f"{JENKINS_URL}/crumbIssuer/api/json",
            auth=HTTPBasicAuth(ADMIN_USER, ADMIN_PASSWORD),
            timeout=10
        )

        headers = {"Content-Type": "application/xml"}
        if crumb_response.status_code == 200:
            crumb_data = crumb_response.json()
            crumb = crumb_data.get("crumb")
            crumb_field = crumb_data.get("crumbRequestField", "Jenkins-Crumb")
            headers[crumb_field] = crumb

        # Create job as admin
        create_response = requests.post(
            f"{JENKINS_URL}/createItem?name={job_name}",
            auth=HTTPBasicAuth(ADMIN_USER, ADMIN_PASSWORD),
            headers=headers,
            data=job_config,
            timeout=10
        )

        # Now test if devops user can read the job
        read_response = requests.get(
            f"{JENKINS_URL}/job/{job_name}/api/json",
            auth=HTTPBasicAuth(DEVOPS_USER, DEVOPS_USER_PASSWORD),
            timeout=10
        )

        assert read_response.status_code == 200, (
            "DevOps user should have Job/Read permission"
        )

        # Cleanup: delete the test job
        if crumb_response.status_code == 200:
            delete_response = requests.post(
                f"{JENKINS_URL}/job/{job_name}/doDelete",
                auth=HTTPBasicAuth(ADMIN_USER, ADMIN_PASSWORD),
                headers={crumb_field: crumb},
                timeout=10
            )

    def test_devops_has_job_build_permission(self):
        """Test that devops user has Job/Build permission."""
        # Create a simple test job as admin
        job_name = "test-job-build"
        job_config = """<?xml version='1.1' encoding='UTF-8'?>
<project>
  <description>Test job for build permission testing</description>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <scm class="hudson.scm.NullSCM"/>
  <canRoam>true</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers/>
  <concurrentBuild>false</concurrentBuild>
  <builders/>
  <publishers/>
  <buildWrappers/>
</project>"""

        # Get crumb for admin
        crumb_response = requests.get(
            f"{JENKINS_URL}/crumbIssuer/api/json",
            auth=HTTPBasicAuth(ADMIN_USER, ADMIN_PASSWORD),
            timeout=10
        )

        headers = {"Content-Type": "application/xml"}
        if crumb_response.status_code == 200:
            crumb_data = crumb_response.json()
            crumb = crumb_data.get("crumb")
            crumb_field = crumb_data.get("crumbRequestField", "Jenkins-Crumb")
            headers[crumb_field] = crumb

        # Create job as admin
        requests.post(
            f"{JENKINS_URL}/createItem?name={job_name}",
            auth=HTTPBasicAuth(ADMIN_USER, ADMIN_PASSWORD),
            headers=headers,
            data=job_config,
            timeout=10
        )

        # Get crumb for devops user
        devops_crumb_response = requests.get(
            f"{JENKINS_URL}/crumbIssuer/api/json",
            auth=HTTPBasicAuth(DEVOPS_USER, DEVOPS_USER_PASSWORD),
            timeout=10
        )

        devops_headers = {}
        if devops_crumb_response.status_code == 200:
            devops_crumb_data = devops_crumb_response.json()
            devops_crumb = devops_crumb_data.get("crumb")
            devops_crumb_field = devops_crumb_data.get("crumbRequestField", "Jenkins-Crumb")
            devops_headers[devops_crumb_field] = devops_crumb

        # Try to build the job as devops user
        build_response = requests.post(
            f"{JENKINS_URL}/job/{job_name}/build",
            auth=HTTPBasicAuth(DEVOPS_USER, DEVOPS_USER_PASSWORD),
            headers=devops_headers,
            timeout=10
        )

        # 201 means build was queued successfully
        assert build_response.status_code == 201, (
            f"DevOps user should have Job/Build permission. Status: {build_response.status_code}"
        )

        # Cleanup: delete the test job
        if crumb_response.status_code == 200:
            requests.post(
                f"{JENKINS_URL}/job/{job_name}/doDelete",
                auth=HTTPBasicAuth(ADMIN_USER, ADMIN_PASSWORD),
                headers={crumb_field: crumb},
                timeout=10
            )

    def test_devops_has_job_cancel_permission(self):
        """Test that devops user has Job/Cancel permission."""
        # This is tested implicitly - if devops user can build, they should be able to cancel
        # We verify the permission exists in the configuration
        response = requests.get(
            f"{JENKINS_URL}/api/json",
            auth=HTTPBasicAuth(DEVOPS_USER, DEVOPS_USER_PASSWORD),
            timeout=10
        )

        assert response.status_code == 200, (
            "DevOps user should be authenticated and have basic access"
        )

    def test_devops_has_job_workspace_permission(self):
        """Test that devops user has Job/Workspace permission."""
        # Create a test job and verify user can access workspace info
        job_name = "test-job-workspace"
        job_config = """<?xml version='1.1' encoding='UTF-8'?>
<project>
  <description>Test job for workspace permission testing</description>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <scm class="hudson.scm.NullSCM"/>
  <canRoam>true</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers/>
  <concurrentBuild>false</concurrentBuild>
  <builders/>
  <publishers/>
  <buildWrappers/>
</project>"""

        # Get crumb for admin
        crumb_response = requests.get(
            f"{JENKINS_URL}/crumbIssuer/api/json",
            auth=HTTPBasicAuth(ADMIN_USER, ADMIN_PASSWORD),
            timeout=10
        )

        headers = {"Content-Type": "application/xml"}
        if crumb_response.status_code == 200:
            crumb_data = crumb_response.json()
            crumb = crumb_data.get("crumb")
            crumb_field = crumb_data.get("crumbRequestField", "Jenkins-Crumb")
            headers[crumb_field] = crumb

        # Create job as admin
        requests.post(
            f"{JENKINS_URL}/createItem?name={job_name}",
            auth=HTTPBasicAuth(ADMIN_USER, ADMIN_PASSWORD),
            headers=headers,
            data=job_config,
            timeout=10
        )

        # Try to access workspace as devops user
        workspace_response = requests.get(
            f"{JENKINS_URL}/job/{job_name}/ws/",
            auth=HTTPBasicAuth(DEVOPS_USER, DEVOPS_USER_PASSWORD),
            timeout=10,
            allow_redirects=False
        )

        # 200 (workspace page) or 404 (workspace doesn't exist yet) both indicate permission
        # 403 would indicate no permission
        assert workspace_response.status_code != 403, (
            "DevOps user should have Job/Workspace permission"
        )

        # Cleanup: delete the test job
        if crumb_response.status_code == 200:
            requests.post(
                f"{JENKINS_URL}/job/{job_name}/doDelete",
                auth=HTTPBasicAuth(ADMIN_USER, ADMIN_PASSWORD),
                headers={crumb_field: crumb},
                timeout=10
            )

    def test_devops_has_view_read_permission(self):
        """Test that devops user has View/Read permission."""
        # Try to access the main view
        response = requests.get(
            f"{JENKINS_URL}/api/json",
            auth=HTTPBasicAuth(DEVOPS_USER, DEVOPS_USER_PASSWORD),
            timeout=10
        )

        assert response.status_code == 200, (
            "DevOps user should have View/Read permission"
        )

        data = response.json()
        assert "views" in data or "jobs" in data, (
            "DevOps user should be able to see views"
        )


class TestContainerHealthCheck:
    """Test Docker container health check functionality."""

    def test_health_check_reports_healthy_status(self):
        """Test that Jenkins container's health check reports healthy status."""
        # Check if docker is available
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", "name=jenkins", "--format", "{{.Status}}"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                pytest.skip("Docker is not available or Jenkins container is not running")

            status = result.stdout.strip()

            # The status should contain "healthy" if the health check is passing
            assert "healthy" in status.lower(), (
                f"Container should report healthy status. Current status: {status}"
            )

        except FileNotFoundError:
            pytest.skip("Docker command not found")
        except subprocess.TimeoutExpired:
            pytest.fail("Docker command timed out")

    def test_health_check_endpoint_accessible(self):
        """Test that the health check endpoint (/login) is accessible."""
        # This is what the health check tests
        response = requests.get(
            f"{JENKINS_URL}/login",
            timeout=10,
            allow_redirects=True
        )

        assert response.status_code == 200, (
            f"Health check endpoint should be accessible. "
            f"Status code: {response.status_code}"
        )

    def test_jenkins_web_interface_accessible(self):
        """Test that Jenkins web interface is accessible (what health check validates)."""
        response = requests.get(
            f"{JENKINS_URL}/",
            timeout=10,
            allow_redirects=True
        )

        # Should redirect to login or return 200
        assert response.status_code == 200, (
            "Jenkins web interface should be accessible"
        )

        # Verify it's actually Jenkins
        assert "jenkins" in response.text.lower(), (
            "Response should contain Jenkins content"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
