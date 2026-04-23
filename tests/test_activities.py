import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Provide a TestClient for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_db():
    """Reset activities to a clean state before each test"""
    initial_state = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        }
    }
    orig = dict(activities)
    activities.clear()
    activities.update(initial_state)
    yield
    activities.clear()
    activities.update(orig)


def test_get_activities(client, reset_db):
    """Test retrieving all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert "Chess Club" in data
    assert data["Chess Club"]["description"] == "Learn strategies and compete in chess tournaments"


def test_get_activities_structure(client, reset_db):
    """Test that activity structure contains required fields"""
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    activity = data["Chess Club"]
    assert "description" in activity
    assert "schedule" in activity
    assert "max_participants" in activity
    assert "participants" in activity
    assert isinstance(activity["participants"], list)


def test_signup_new_student(client, reset_db):
    """Test signing up a new student for an activity"""
    response = client.post(
        "/activities/Chess Club/signup?email=newstudent@mergington.edu"
    )
    assert response.status_code == 200
    assert "Signed up newstudent@mergington.edu" in response.json()["message"]
    
    # Verify the student was added
    activities_response = client.get("/activities")
    participants = activities_response.json()["Chess Club"]["participants"]
    assert "newstudent@mergington.edu" in participants


def test_signup_activity_not_found(client, reset_db):
    """Test signing up for a non-existent activity"""
    response = client.post(
        "/activities/NonExistent/signup?email=student@mergington.edu"
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_student_already_signed_up(client, reset_db):
    """Test that a student cannot sign up for multiple activities"""
    # First signup
    response1 = client.post(
        "/activities/Chess Club/signup?email=unique@mergington.edu"
    )
    assert response1.status_code == 200
    
    # Second signup should fail
    response2 = client.post(
        "/activities/Chess Club/signup?email=unique@mergington.edu"
    )
    assert response2.status_code == 400
    assert "already signed up" in response2.json()["detail"]


def test_unregister_student(client, reset_db):
    """Test removing a student from an activity"""
    # First add a student
    client.post("/activities/Chess Club/signup?email=test@mergington.edu")
    
    # Then remove them
    response = client.delete(
        "/activities/Chess Club/unregister?email=test@mergington.edu"
    )
    assert response.status_code == 200
    assert "Removed test@mergington.edu" in response.json()["message"]
    
    # Verify student was removed
    activities_response = client.get("/activities")
    participants = activities_response.json()["Chess Club"]["participants"]
    assert "test@mergington.edu" not in participants


def test_unregister_activity_not_found(client, reset_db):
    """Test unregistering from a non-existent activity"""
    response = client.delete(
        "/activities/NonExistent/unregister?email=student@mergington.edu"
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_student_not_registered(client, reset_db):
    """Test unregistering a student who is not registered"""
    response = client.delete(
        "/activities/Chess Club/unregister?email=notstudent@mergington.edu"
    )
    assert response.status_code == 400
    assert "not registered" in response.json()["detail"]


def test_signup_updates_participant_count(client, reset_db):
    """Test that signing up updates the participant count correctly"""
    activities_before = client.get("/activities").json()
    count_before = len(activities_before["Chess Club"]["participants"])
    
    client.post("/activities/Chess Club/signup?email=newmember@mergington.edu")
    
    activities_after = client.get("/activities").json()
    count_after = len(activities_after["Chess Club"]["participants"])
    
    assert count_after == count_before + 1


def test_unregister_updates_participant_count(client, reset_db):
    """Test that unregistering updates the participant count correctly"""
    # Add a student first
    client.post("/activities/Chess Club/signup?email=temporary@mergington.edu")
    
    activities_before = client.get("/activities").json()
    count_before = len(activities_before["Chess Club"]["participants"])
    
    client.delete("/activities/Chess Club/unregister?email=temporary@mergington.edu")
    
    activities_after = client.get("/activities").json()
    count_after = len(activities_after["Chess Club"]["participants"])
    
    assert count_after == count_before - 1
