"""
Integration tests for agenda API endpoints
Tests complete API workflows, HTTP status codes, and response formats
"""
import pytest
import requests
import json
from datetime import time, date
from typing import Dict, Any

# Test configuration
BASE_URL = "http://localhost:8081"
TEST_USER_ID = "test_user_123"

# Test data
TEST_USER_DATA = {
    "email": "agenda_test@example.com",
    "first_name": "Agenda",
    "last_name": "Tester",
    "phone": "+381123456789"
}

TEST_EVENT_DATA = {
    "name": "Integration Test Wedding",
    "plan": "freemium",
    "location": "Belgrade, Serbia",
    "restaurant_name": "Test Restaurant",
    "date": "2024-06-15",
    "time": "18:00",
    "event_type": "wedding",
    "expected_guests": 100,
    "description": "Integration test event"
}

TEST_AGENDA_DATA = {
    "title": "Wedding Program",
    "description": "Complete wedding program"
}

TEST_AGENDA_ITEM_DATA = {
    "title": "Wedding Ceremony",
    "description": "Main wedding ceremony",
    "start_time": "16:00",
    "end_time": "17:00",
    "location": "Main Hall",
    "type": "ceremony",
    "is_important": True
}


class TestAgendaAPIIntegration:
    """Integration tests for agenda API endpoints"""
    
    @classmethod
    def setup_class(cls):
        """Set up test data before running tests"""
        cls.headers = {"Authorization": f"Bearer {TEST_USER_ID}"}
        cls.event_id = None
        cls.agenda_id = None
        cls.agenda_item_ids = []
        
        # Create test user
        try:
            response = requests.post(
                f"{BASE_URL}/users",
                json=TEST_USER_DATA,
                headers={"Content-Type": "application/json"}
            )
            print(f"User creation: {response.status_code}")
        except requests.exceptions.RequestException:
            print("Warning: Could not create user (may already exist or server not running)")
        
        # Create test event
        try:
            response = requests.post(
                f"{BASE_URL}/events",
                json=TEST_EVENT_DATA,
                headers={**cls.headers, "Content-Type": "application/json"}
            )
            if response.status_code == 201:
                cls.event_id = response.json()["event"]["id"]
                print(f"Created test event: {cls.event_id}")
            else:
                print(f"Failed to create event: {response.status_code} - {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Warning: Could not create event: {e}")
    
    def test_server_health(self):
        """Test that the server is running"""
        try:
            response = requests.get(f"{BASE_URL}/health-check")
            assert response.status_code == 200
            print("✓ Server is running")
        except requests.exceptions.RequestException:
            pytest.skip("Server is not running - skipping integration tests")
    
    def test_create_agenda_success(self):
        """Test successful agenda creation"""
        if not self.event_id:
            pytest.skip("No test event available")
        
        response = requests.post(
            f"{BASE_URL}/events/{self.event_id}/agenda",
            json=TEST_AGENDA_DATA,
            headers={**self.headers, "Content-Type": "application/json"}
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert "agenda" in data
        assert data["agenda"]["title"] == TEST_AGENDA_DATA["title"]
        assert data["agenda"]["description"] == TEST_AGENDA_DATA["description"]
        assert data["agenda"]["event_id"] == self.event_id
        assert len(data["agenda"]["id"]) == 12  # NanoID length
        
        self.__class__.agenda_id = data["agenda"]["id"]
        print(f"✓ Created agenda: {self.agenda_id}")
    
    def test_create_agenda_duplicate(self):
        """Test creating duplicate agenda returns 409"""
        if not self.event_id:
            pytest.skip("No test event available")
        
        response = requests.post(
            f"{BASE_URL}/events/{self.event_id}/agenda",
            json=TEST_AGENDA_DATA,
            headers={**self.headers, "Content-Type": "application/json"}
        )
        
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]
        print("✓ Duplicate agenda creation properly rejected")
    
    def test_get_agenda_success(self):
        """Test successful agenda retrieval"""
        if not self.event_id:
            pytest.skip("No test event available")
        
        response = requests.get(
            f"{BASE_URL}/events/{self.event_id}/agenda",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "agenda" in data
        assert data["agenda"]["id"] == self.agenda_id
        assert data["agenda"]["title"] == TEST_AGENDA_DATA["title"]
        assert "items" in data["agenda"]
        assert isinstance(data["agenda"]["items"], list)
        print("✓ Retrieved agenda successfully")
    
    def test_get_agenda_not_found(self):
        """Test agenda retrieval for nonexistent event"""
        fake_event_id = "fake_event_id"
        
        response = requests.get(
            f"{BASE_URL}/events/{fake_event_id}/agenda",
            headers=self.headers
        )
        
        assert response.status_code == 403  # Permission denied for non-owned event
        print("✓ Non-existent agenda properly returns 403")
    
    def test_update_agenda_success(self):
        """Test successful agenda update"""
        if not self.event_id:
            pytest.skip("No test event available")
        
        update_data = {
            "title": "Updated Wedding Program",
            "description": "Updated description"
        }
        
        response = requests.put(
            f"{BASE_URL}/events/{self.event_id}/agenda",
            json=update_data,
            headers={**self.headers, "Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["agenda"]["title"] == update_data["title"]
        assert data["agenda"]["description"] == update_data["description"]
        print("✓ Updated agenda successfully")
    
    def test_create_agenda_item_success(self):
        """Test successful agenda item creation"""
        if not self.event_id:
            pytest.skip("No test event available")
        
        response = requests.post(
            f"{BASE_URL}/events/{self.event_id}/agenda/items",
            json=TEST_AGENDA_ITEM_DATA,
            headers={**self.headers, "Content-Type": "application/json"}
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert "agenda_item" in data
        item = data["agenda_item"]
        assert item["title"] == TEST_AGENDA_ITEM_DATA["title"]
        assert item["start_time"] == TEST_AGENDA_ITEM_DATA["start_time"]
        assert item["type"] == TEST_AGENDA_ITEM_DATA["type"]
        assert item["is_important"] == TEST_AGENDA_ITEM_DATA["is_important"]
        assert len(item["id"]) == 12  # NanoID length
        
        self.__class__.agenda_item_ids.append(item["id"])
        print(f"✓ Created agenda item: {item['id']}")
    
    def test_create_multiple_agenda_items(self):
        """Test creating multiple agenda items with auto-ordering"""
        if not self.event_id:
            pytest.skip("No test event available")
        
        items_data = [
            {
                "title": "Reception",
                "start_time": "18:00",
                "end_time": "22:00",
                "type": "reception",
                "is_important": False
            },
            {
                "title": "First Dance",
                "start_time": "19:00",
                "end_time": "19:30",
                "type": "entertainment",
                "is_important": True
            },
            {
                "title": "Dinner",
                "start_time": "20:00",
                "end_time": "21:00",
                "type": "meal",
                "is_important": False
            }
        ]
        
        for item_data in items_data:
            response = requests.post(
                f"{BASE_URL}/events/{self.event_id}/agenda/items",
                json=item_data,
                headers={**self.headers, "Content-Type": "application/json"}
            )
            
            assert response.status_code == 201
            item_id = response.json()["agenda_item"]["id"]
            self.__class__.agenda_item_ids.append(item_id)
        
        print(f"✓ Created {len(items_data)} additional agenda items")
    
    def test_create_agenda_item_invalid_time(self):
        """Test agenda item creation with invalid time range"""
        if not self.event_id:
            pytest.skip("No test event available")
        
        invalid_item_data = {
            "title": "Invalid Time Item",
            "start_time": "18:00",
            "end_time": "17:00",  # End before start
            "type": "other"
        }
        
        response = requests.post(
            f"{BASE_URL}/events/{self.event_id}/agenda/items",
            json=invalid_item_data,
            headers={**self.headers, "Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
        assert "End time must be after start time" in response.json()["detail"]
        print("✓ Invalid time range properly rejected")
    
    def test_get_agenda_with_items(self):
        """Test retrieving agenda with all items ordered correctly"""
        if not self.event_id:
            pytest.skip("No test event available")
        
        response = requests.get(
            f"{BASE_URL}/events/{self.event_id}/agenda",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        items = data["agenda"]["items"]
        assert len(items) == len(self.agenda_item_ids)
        
        # Check that items are ordered by display_order
        for i in range(len(items) - 1):
            assert items[i]["display_order"] <= items[i + 1]["display_order"]
        
        print(f"✓ Retrieved agenda with {len(items)} items in correct order")
    
    def test_update_agenda_item_success(self):
        """Test successful agenda item update"""
        if not self.event_id or not self.agenda_item_ids:
            pytest.skip("No test data available")
        
        item_id = self.agenda_item_ids[0]
        update_data = {
            "title": "Updated Ceremony",
            "location": "Updated Location",
            "is_important": False
        }
        
        response = requests.put(
            f"{BASE_URL}/events/{self.event_id}/agenda/items/{item_id}",
            json=update_data,
            headers={**self.headers, "Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        item = data["agenda_item"]
        assert item["title"] == update_data["title"]
        assert item["location"] == update_data["location"]
        assert item["is_important"] == update_data["is_important"]
        print("✓ Updated agenda item successfully")
    
    def test_reorder_agenda_items_success(self):
        """Test successful agenda item reordering"""
        if not self.event_id or len(self.agenda_item_ids) < 3:
            pytest.skip("Not enough test data available")
        
        # Reverse the order of first 3 items
        reorder_data = {
            "items": [
                {"item_id": self.agenda_item_ids[2], "display_order": 1},
                {"item_id": self.agenda_item_ids[1], "display_order": 2},
                {"item_id": self.agenda_item_ids[0], "display_order": 3}
            ]
        }
        
        response = requests.put(
            f"{BASE_URL}/events/{self.event_id}/agenda/reorder",
            json=reorder_data,
            headers={**self.headers, "Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        assert "successfully reordered" in response.json()["detail"]
        
        # Verify the new order
        response = requests.get(
            f"{BASE_URL}/events/{self.event_id}/agenda",
            headers=self.headers
        )
        
        items = response.json()["agenda"]["items"]
        assert items[0]["id"] == self.agenda_item_ids[2]
        assert items[1]["id"] == self.agenda_item_ids[1]
        assert items[2]["id"] == self.agenda_item_ids[0]
        
        print("✓ Reordered agenda items successfully")
    
    def test_reorder_agenda_items_invalid_ids(self):
        """Test reordering with invalid item IDs"""
        if not self.event_id:
            pytest.skip("No test event available")
        
        reorder_data = {
            "items": [
                {"item_id": "invalid_item_id", "display_order": 1}
            ]
        }
        
        response = requests.put(
            f"{BASE_URL}/events/{self.event_id}/agenda/reorder",
            json=reorder_data,
            headers={**self.headers, "Content-Type": "application/json"}
        )
        
        assert response.status_code == 400
        assert "don't belong to the specified agenda" in response.json()["detail"]
        print("✓ Invalid reorder request properly rejected")
    
    def test_delete_agenda_item_success(self):
        """Test successful agenda item deletion"""
        if not self.event_id or not self.agenda_item_ids:
            pytest.skip("No test data available")
        
        item_id = self.agenda_item_ids[-1]  # Delete last item
        
        response = requests.delete(
            f"{BASE_URL}/events/{self.event_id}/agenda/items/{item_id}",
            headers=self.headers
        )
        
        assert response.status_code == 204
        
        # Verify item is deleted
        response = requests.get(
            f"{BASE_URL}/events/{self.event_id}/agenda",
            headers=self.headers
        )
        
        items = response.json()["agenda"]["items"]
        item_ids = [item["id"] for item in items]
        assert item_id not in item_ids
        
        self.__class__.agenda_item_ids.remove(item_id)
        print("✓ Deleted agenda item successfully")
    
    def test_delete_agenda_item_not_found(self):
        """Test deleting nonexistent agenda item"""
        if not self.event_id:
            pytest.skip("No test event available")
        
        fake_item_id = "fake_item_id"
        
        response = requests.delete(
            f"{BASE_URL}/events/{self.event_id}/agenda/items/{fake_item_id}",
            headers=self.headers
        )
        
        assert response.status_code == 404
        print("✓ Non-existent item deletion properly returns 404")
    
    def test_unauthorized_access(self):
        """Test unauthorized access to agenda endpoints"""
        if not self.event_id:
            pytest.skip("No test event available")
        
        wrong_headers = {"Authorization": "Bearer wrong_user_id"}
        
        # Test all endpoints with wrong user
        endpoints = [
            ("GET", f"/events/{self.event_id}/agenda"),
            ("POST", f"/events/{self.event_id}/agenda", TEST_AGENDA_DATA),
            ("PUT", f"/events/{self.event_id}/agenda", {"title": "Test"}),
            ("DELETE", f"/events/{self.event_id}/agenda"),
            ("POST", f"/events/{self.event_id}/agenda/items", TEST_AGENDA_ITEM_DATA),
        ]
        
        if self.agenda_item_ids:
            item_id = self.agenda_item_ids[0]
            endpoints.extend([
                ("PUT", f"/events/{self.event_id}/agenda/items/{item_id}", {"title": "Test"}),
                ("DELETE", f"/events/{self.event_id}/agenda/items/{item_id}"),
            ])
        
        for method, endpoint, *data in endpoints:
            json_data = data[0] if data else None
            headers = {**wrong_headers, "Content-Type": "application/json"} if json_data else wrong_headers
            
            response = requests.request(method, f"{BASE_URL}{endpoint}", json=json_data, headers=headers)
            assert response.status_code in [403, 404]  # Forbidden or Not Found
        
        print("✓ Unauthorized access properly rejected for all endpoints")
    
    def test_delete_agenda_cascade(self):
        """Test agenda deletion cascades to items"""
        if not self.event_id:
            pytest.skip("No test event available")
        
        # Get current item count
        response = requests.get(
            f"{BASE_URL}/events/{self.event_id}/agenda",
            headers=self.headers
        )
        items_before = len(response.json()["agenda"]["items"])
        
        # Delete agenda
        response = requests.delete(
            f"{BASE_URL}/events/{self.event_id}/agenda",
            headers=self.headers
        )
        
        assert response.status_code == 204
        
        # Verify agenda is deleted
        response = requests.get(
            f"{BASE_URL}/events/{self.event_id}/agenda",
            headers=self.headers
        )
        
        assert response.status_code == 404
        print(f"✓ Deleted agenda and {items_before} items via cascade")
    
    def test_complete_workflow(self):
        """Test complete agenda management workflow"""
        if not self.event_id:
            pytest.skip("No test event available")
        
        # 1. Create agenda
        agenda_data = {"title": "Workflow Test Agenda"}
        response = requests.post(
            f"{BASE_URL}/events/{self.event_id}/agenda",
            json=agenda_data,
            headers={**self.headers, "Content-Type": "application/json"}
        )
        assert response.status_code == 201
        
        # 2. Add multiple items
        items_data = [
            {"title": "Item 1", "start_time": "10:00", "type": "ceremony"},
            {"title": "Item 2", "start_time": "11:00", "type": "reception"},
            {"title": "Item 3", "start_time": "12:00", "type": "meal"}
        ]
        
        item_ids = []
        for item_data in items_data:
            response = requests.post(
                f"{BASE_URL}/events/{self.event_id}/agenda/items",
                json=item_data,
                headers={**self.headers, "Content-Type": "application/json"}
            )
            assert response.status_code == 201
            item_ids.append(response.json()["agenda_item"]["id"])
        
        # 3. Reorder items
        reorder_data = {
            "items": [
                {"item_id": item_ids[2], "display_order": 1},
                {"item_id": item_ids[0], "display_order": 2},
                {"item_id": item_ids[1], "display_order": 3}
            ]
        }
        
        response = requests.put(
            f"{BASE_URL}/events/{self.event_id}/agenda/reorder",
            json=reorder_data,
            headers={**self.headers, "Content-Type": "application/json"}
        )
        assert response.status_code == 200
        
        # 4. Update an item
        response = requests.put(
            f"{BASE_URL}/events/{self.event_id}/agenda/items/{item_ids[0]}",
            json={"title": "Updated Item 1"},
            headers={**self.headers, "Content-Type": "application/json"}
        )
        assert response.status_code == 200
        
        # 5. Delete an item
        response = requests.delete(
            f"{BASE_URL}/events/{self.event_id}/agenda/items/{item_ids[1]}",
            headers=self.headers
        )
        assert response.status_code == 204
        
        # 6. Verify final state
        response = requests.get(
            f"{BASE_URL}/events/{self.event_id}/agenda",
            headers=self.headers
        )
        assert response.status_code == 200
        
        final_items = response.json()["agenda"]["items"]
        assert len(final_items) == 2  # One deleted
        assert final_items[0]["title"] == "Item 3"  # Reordered to first
        assert final_items[1]["title"] == "Updated Item 1"  # Updated title
        
        print("✓ Complete workflow executed successfully")


if __name__ == "__main__":
    # Run with: python -m pytest tests/test_agenda_integration.py -v -s
    pytest.main([__file__, "-v", "-s"])