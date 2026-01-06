"""Tests for the FastAPI Mergington High School application"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirect(self, client):
        """Test that root redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestActivitiesEndpoint:
    """Tests for the activities endpoint"""

    def test_get_activities(self, client):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        activities = response.json()
        
        # Verify structure and expected activities
        assert isinstance(activities, dict)
        assert "Chess Club" in activities
        assert "Programming Class" in activities
        assert "Basketball" in activities
        
        # Verify activity structure
        chess_club = activities["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)

    def test_activities_have_participants(self, client):
        """Test that activities have participant data"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity in activities.items():
            assert "participants" in activity
            assert isinstance(activity["participants"], list)


class TestSignupEndpoint:
    """Tests for the signup endpoint"""

    def test_signup_for_activity(self, client):
        """Test signing up a new student for an activity"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
        assert "newstudent@mergington.edu" in response.json()["message"]

    def test_signup_nonexistent_activity(self, client):
        """Test signup fails for non-existent activity"""
        response = client.post(
            "/activities/Fake Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_duplicate_student(self, client):
        """Test that duplicate signup is rejected"""
        email = "michael@mergington.edu"  # Already in Chess Club
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_multiple_activities_signup(self, client):
        """Test a student can sign up for multiple activities"""
        email = "newstudent2@mergington.edu"
        
        # Signup for first activity
        response1 = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Signup for second activity
        response2 = client.post(
            "/activities/Programming Class/signup",
            params={"email": email}
        )
        assert response2.status_code == 200
        
        # Verify both signups
        activities = client.get("/activities").json()
        assert email in activities["Chess Club"]["participants"]
        assert email in activities["Programming Class"]["participants"]


class TestUnregisterEndpoint:
    """Tests for the unregister endpoint"""

    def test_unregister_from_activity(self, client):
        """Test unregistering a student from an activity"""
        # First signup
        client.post(
            "/activities/Tennis Club/signup",
            params={"email": "student@mergington.edu"}
        )
        
        # Then unregister
        response = client.delete(
            "/activities/Tennis Club/unregister",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]

    def test_unregister_nonexistent_activity(self, client):
        """Test unregister fails for non-existent activity"""
        response = client.delete(
            "/activities/Fake Club/unregister",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_not_registered_student(self, client):
        """Test unregister fails if student isn't signed up"""
        response = client.delete(
            "/activities/Basketball/unregister",
            params={"email": "notstudent@mergington.edu"}
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]


class TestActivityValidation:
    """Tests for activity data validation"""

    def test_all_activities_have_required_fields(self, client):
        """Test that all activities have required fields"""
        response = client.get("/activities")
        activities = response.json()
        
        required_fields = {"description", "schedule", "max_participants", "participants"}
        
        for activity_name, activity in activities.items():
            for field in required_fields:
                assert field in activity, f"Activity '{activity_name}' missing '{field}'"

    def test_max_participants_is_positive(self, client):
        """Test that max_participants is a positive number"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity in activities.items():
            assert activity["max_participants"] > 0, \
                f"Activity '{activity_name}' has invalid max_participants"

    def test_participants_count_within_limit(self, client):
        """Test that current participants don't exceed max"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity in activities.items():
            assert len(activity["participants"]) <= activity["max_participants"], \
                f"Activity '{activity_name}' exceeds max participants"
