"""
Comprehensive tests for agenda functionality
Tests cover DAO methods, API endpoints, ownership validation, cascade deletion, and error handling
"""
import pytest
import requests
from datetime import time, date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from app.database.db import Base, get_db
from app.database.models import User, Event, Agenda, AgendaItem, AgendaItemType
from app.database.daos import UserQuery, EventQuery, AgendaQuery, AgendaItemQuery
from app.api.services import AgendaLogic
from app.api.models import (
    AgendaCreate, AgendaUpdate, AgendaItemCreate, AgendaItemUpdate, 
    AgendaReorderRequest, ReorderItem, AgendaItemType as APIAgendaItemType
)
from app.utils.nanoid import generate_user_id, generate_event_id, generate_agenda_id, generate_agenda_item_id


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@pytest.fixture
def db_session():
    """Create a test database session"""
    Base.metadata.create_all(bind=engine)
    session = Session(bind=engine)
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(db_session):
    """Create a test user"""
    user = User(
        id=generate_user_id(),
        email="test@example.com",
        first_name="Test",
        last_name="User",
        phone="+381123456789"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_event(db_session, test_user):
    """Create a test event"""
    event = Event(
        id=generate_event_id(),
        name="Test Wedding",
        plan="freemium",
        location="Belgrade, Serbia",
        restaurant_name="Test Restaurant",
        date=date(2024, 6, 15),
        time=time(18, 0),
        event_type="wedding",
        expected_guests=100,
        description="Test wedding event",
        owner_id=test_user.id,
        status="draft"
    )
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)
    return event


@pytest.fixture
def test_agenda(db_session, test_event):
    """Create a test agenda"""
    agenda = Agenda(
        id=generate_agenda_id(),
        event_id=test_event.id,
        title="Test Program",
        description="Test agenda description"
    )
    db_session.add(agenda)
    db_session.commit()
    db_session.refresh(agenda)
    return agenda


@pytest.fixture
def test_agenda_items(db_session, test_agenda):
    """Create test agenda items"""
    items = []
    item_data = [
        {
            "title": "Ceremony",
            "start_time": time(16, 0),
            "end_time": time(17, 0),
            "type": AgendaItemType.ceremony,
            "display_order": 1,
            "is_important": True
        },
        {
            "title": "Reception",
            "start_time": time(18, 0),
            "end_time": time(22, 0),
            "type": AgendaItemType.reception,
            "display_order": 2,
            "is_important": False
        },
        {
            "title": "Entertainment",
            "start_time": time(20, 0),
            "end_time": time(21, 0),
            "type": AgendaItemType.entertainment,
            "display_order": 3,
            "is_important": False
        }
    ]
    
    for data in item_data:
        item = AgendaItem(
            id=generate_agenda_item_id(),
            agenda_id=test_agenda.id,
            **data
        )
        db_session.add(item)
        items.append(item)
    
    db_session.commit()
    for item in items:
        db_session.refresh(item)
    return items


class TestAgendaQuery:
    """Unit tests for AgendaQuery DAO methods"""
    
    def test_get_one_success(self, db_session, test_agenda, test_user, test_event):
        """Test successful agenda retrieval"""
        agenda_query = AgendaQuery()
        result = agenda_query.get_one(db_session, test_event.id, test_user.id)
        
        assert result is not None
        assert result.id == test_agenda.id
        assert result.event_id == test_event.id
        assert result.title == "Test Program"
    
    def test_get_one_wrong_user(self, db_session, test_agenda, test_event):
        """Test agenda retrieval with wrong user"""
        agenda_query = AgendaQuery()
        wrong_user_id = generate_user_id()
        result = agenda_query.get_one(db_session, test_event.id, wrong_user_id)
        
        assert result is None
    
    def test_get_one_nonexistent_event(self, db_session, test_user):
        """Test agenda retrieval for nonexistent event"""
        agenda_query = AgendaQuery()
        fake_event_id = generate_event_id()
        result = agenda_query.get_one(db_session, fake_event_id, test_user.id)
        
        assert result is None
    
    def test_get_agenda_with_items(self, db_session, test_agenda, test_agenda_items, test_user, test_event):
        """Test agenda retrieval with items ordered correctly"""
        agenda_query = AgendaQuery()
        result = agenda_query.get_agenda_with_items(db_session, test_event.id, test_user.id)
        
        assert result is not None
        assert result.id == test_agenda.id
        assert len(result.items) == 3
        
        # Check ordering by display_order
        assert result.items[0].display_order == 1
        assert result.items[1].display_order == 2
        assert result.items[2].display_order == 3
        
        # Check item details
        assert result.items[0].title == "Ceremony"
        assert result.items[0].is_important is True
        assert result.items[1].title == "Reception"
        assert result.items[2].title == "Entertainment"
    
    def test_create_agenda_success(self, db_session, test_event, test_user):
        """Test successful agenda creation"""
        agenda_query = AgendaQuery()
        result = agenda_query.create(
            db_session, 
            test_event.id, 
            test_user.id, 
            "New Agenda", 
            "New description"
        )
        
        assert result is not None
        assert result.event_id == test_event.id
        assert result.title == "New Agenda"
        assert result.description == "New description"
        assert len(result.id) == 12  # NanoID length
    
    def test_create_agenda_default_title(self, db_session, test_event, test_user):
        """Test agenda creation with default title"""
        agenda_query = AgendaQuery()
        result = agenda_query.create(db_session, test_event.id, test_user.id)
        
        assert result is not None
        assert result.title == "Program događaja"
        assert result.description is None
    
    def test_create_agenda_wrong_user(self, db_session, test_event):
        """Test agenda creation with wrong user"""
        agenda_query = AgendaQuery()
        wrong_user_id = generate_user_id()
        result = agenda_query.create(db_session, test_event.id, wrong_user_id, "Test")
        
        assert result is None
    
    def test_update_agenda_success(self, db_session, test_agenda, test_user, test_event):
        """Test successful agenda update"""
        agenda_query = AgendaQuery()
        result = agenda_query.update(
            db_session, 
            test_event.id, 
            test_user.id, 
            "Updated Title", 
            "Updated description"
        )
        
        assert result is not None
        assert result.title == "Updated Title"
        assert result.description == "Updated description"
    
    def test_update_agenda_partial(self, db_session, test_agenda, test_user, test_event):
        """Test partial agenda update"""
        agenda_query = AgendaQuery()
        original_description = test_agenda.description
        
        result = agenda_query.update(db_session, test_event.id, test_user.id, "New Title", None)
        
        assert result is not None
        assert result.title == "New Title"
        assert result.description == original_description
    
    def test_delete_agenda_success(self, db_session, test_agenda, test_user, test_event):
        """Test successful agenda deletion"""
        agenda_query = AgendaQuery()
        result = agenda_query.delete(db_session, test_event.id, test_user.id)
        
        assert result is True
        
        # Verify agenda is deleted
        deleted_agenda = agenda_query.get_one(db_session, test_event.id, test_user.id)
        assert deleted_agenda is None
    
    def test_delete_agenda_cascade_items(self, db_session, test_agenda, test_agenda_items, test_user, test_event):
        """Test agenda deletion cascades to items"""
        agenda_query = AgendaQuery()
        agenda_item_query = AgendaItemQuery()
        
        # Verify items exist before deletion
        items_before = agenda_item_query.get_all_for_agenda(db_session, test_event.id, test_user.id)
        assert len(items_before) == 3
        
        # Delete agenda
        result = agenda_query.delete(db_session, test_event.id, test_user.id)
        assert result is True
        
        # Verify items are also deleted
        items_after = agenda_item_query.get_all_for_agenda(db_session, test_event.id, test_user.id)
        assert len(items_after) == 0
    
    def test_validate_ownership_success(self, db_session, test_user, test_event):
        """Test successful ownership validation"""
        agenda_query = AgendaQuery()
        result = agenda_query.validate_ownership(db_session, test_event.id, test_user.id)
        
        assert result is True
    
    def test_validate_ownership_failure(self, db_session, test_event):
        """Test ownership validation failure"""
        agenda_query = AgendaQuery()
        wrong_user_id = generate_user_id()
        result = agenda_query.validate_ownership(db_session, test_event.id, wrong_user_id)
        
        assert result is False


class TestAgendaItemQuery:
    """Unit tests for AgendaItemQuery DAO methods"""
    
    def test_get_one_success(self, db_session, test_agenda_items, test_user, test_event):
        """Test successful agenda item retrieval"""
        agenda_item_query = AgendaItemQuery()
        item = test_agenda_items[0]
        
        result = agenda_item_query.get_one(db_session, item.id, test_event.id, test_user.id)
        
        assert result is not None
        assert result.id == item.id
        assert result.title == "Ceremony"
        assert result.is_important is True
    
    def test_get_one_wrong_user(self, db_session, test_agenda_items, test_event):
        """Test agenda item retrieval with wrong user"""
        agenda_item_query = AgendaItemQuery()
        item = test_agenda_items[0]
        wrong_user_id = generate_user_id()
        
        result = agenda_item_query.get_one(db_session, item.id, test_event.id, wrong_user_id)
        
        assert result is None
    
    def test_get_all_for_agenda(self, db_session, test_agenda_items, test_user, test_event):
        """Test retrieving all items for agenda"""
        agenda_item_query = AgendaItemQuery()
        
        result = agenda_item_query.get_all_for_agenda(db_session, test_event.id, test_user.id)
        
        assert len(result) == 3
        assert result[0].display_order == 1
        assert result[1].display_order == 2
        assert result[2].display_order == 3
    
    def test_create_agenda_item_success(self, db_session, test_agenda, test_user, test_event):
        """Test successful agenda item creation"""
        agenda_item_query = AgendaItemQuery()
        
        item_data = {
            "title": "New Item",
            "description": "New item description",
            "start_time": time(19, 0),
            "end_time": time(20, 0),
            "location": "Main Hall",
            "type": "speech",
            "is_important": True
        }
        
        result = agenda_item_query.create(db_session, test_event.id, test_user.id, item_data)
        
        assert result is not None
        assert result.title == "New Item"
        assert result.start_time == time(19, 0)
        assert result.type == AgendaItemType.speech
        assert result.is_important is True
        assert result.display_order == 1  # Auto-assigned
    
    def test_create_agenda_item_auto_order(self, db_session, test_agenda, test_agenda_items, test_user, test_event):
        """Test auto-assignment of display_order"""
        agenda_item_query = AgendaItemQuery()
        
        item_data = {
            "title": "Fourth Item",
            "start_time": time(22, 0),
            "type": "other"
        }
        
        result = agenda_item_query.create(db_session, test_event.id, test_user.id, item_data)
        
        assert result is not None
        assert result.display_order == 4  # Should be max + 1
    
    def test_create_agenda_item_no_agenda(self, db_session, test_user):
        """Test agenda item creation when agenda doesn't exist"""
        agenda_item_query = AgendaItemQuery()
        fake_event_id = generate_event_id()
        
        item_data = {
            "title": "Test Item",
            "start_time": time(19, 0),
            "type": "other"
        }
        
        result = agenda_item_query.create(db_session, fake_event_id, test_user.id, item_data)
        
        assert result is None
    
    def test_update_agenda_item_success(self, db_session, test_agenda_items, test_user, test_event):
        """Test successful agenda item update"""
        agenda_item_query = AgendaItemQuery()
        item = test_agenda_items[0]
        
        update_data = {
            "title": "Updated Ceremony",
            "location": "Updated Location",
            "is_important": False
        }
        
        result = agenda_item_query.update(db_session, item.id, test_event.id, test_user.id, update_data)
        
        assert result is not None
        assert result.title == "Updated Ceremony"
        assert result.location == "Updated Location"
        assert result.is_important is False
        # Other fields should remain unchanged
        assert result.start_time == time(16, 0)
        assert result.type == AgendaItemType.ceremony
    
    def test_delete_agenda_item_success(self, db_session, test_agenda_items, test_user, test_event):
        """Test successful agenda item deletion"""
        agenda_item_query = AgendaItemQuery()
        item = test_agenda_items[0]
        
        result = agenda_item_query.delete(db_session, item.id, test_event.id, test_user.id)
        
        assert result is True
        
        # Verify item is deleted
        deleted_item = agenda_item_query.get_one(db_session, item.id, test_event.id, test_user.id)
        assert deleted_item is None
    
    def test_bulk_reorder_success(self, db_session, test_agenda_items, test_user, test_event):
        """Test successful bulk reordering"""
        agenda_item_query = AgendaItemQuery()
        
        # Reverse the order
        item_orders = [
            {"item_id": test_agenda_items[2].id, "display_order": 1},
            {"item_id": test_agenda_items[1].id, "display_order": 2},
            {"item_id": test_agenda_items[0].id, "display_order": 3}
        ]
        
        result = agenda_item_query.bulk_reorder(db_session, test_event.id, test_user.id, item_orders)
        
        assert result is True
        
        # Verify new order
        items = agenda_item_query.get_all_for_agenda(db_session, test_event.id, test_user.id)
        assert items[0].title == "Entertainment"  # Was 3rd, now 1st
        assert items[1].title == "Reception"      # Was 2nd, stays 2nd
        assert items[2].title == "Ceremony"      # Was 1st, now 3rd
    
    def test_bulk_reorder_invalid_items(self, db_session, test_agenda_items, test_user, test_event):
        """Test bulk reordering with invalid item IDs"""
        agenda_item_query = AgendaItemQuery()
        
        item_orders = [
            {"item_id": generate_agenda_item_id(), "display_order": 1},  # Invalid ID
            {"item_id": test_agenda_items[0].id, "display_order": 2}
        ]
        
        result = agenda_item_query.bulk_reorder(db_session, test_event.id, test_user.id, item_orders)
        
        assert result is None
    
    def test_validate_ownership_success(self, db_session, test_agenda_items, test_user, test_event):
        """Test successful item ownership validation"""
        agenda_item_query = AgendaItemQuery()
        item = test_agenda_items[0]
        
        result = agenda_item_query.validate_ownership(db_session, item.id, test_event.id, test_user.id)
        
        assert result is True
    
    def test_validate_ownership_failure(self, db_session, test_agenda_items, test_event):
        """Test item ownership validation failure"""
        agenda_item_query = AgendaItemQuery()
        item = test_agenda_items[0]
        wrong_user_id = generate_user_id()
        
        result = agenda_item_query.validate_ownership(db_session, item.id, test_event.id, wrong_user_id)
        
        assert result is False


class TestAgendaLogic:
    """Unit tests for AgendaLogic service layer"""
    
    def test_get_agenda_success(self, db_session, test_agenda, test_agenda_items, test_user, test_event):
        """Test successful agenda retrieval through service"""
        agenda_logic = AgendaLogic()
        
        status, response = agenda_logic.get_agenda(db_session, test_event.id, test_user.id)
        
        assert status == 200
        assert response.agenda.id == test_agenda.id
        assert len(response.agenda.items) == 3
    
    def test_get_agenda_no_permission(self, db_session, test_agenda, test_event):
        """Test agenda retrieval without permission"""
        agenda_logic = AgendaLogic()
        wrong_user_id = generate_user_id()
        
        with pytest.raises(Exception) as exc_info:
            agenda_logic.get_agenda(db_session, test_event.id, wrong_user_id)
        
        assert "permission" in str(exc_info.value)
    
    def test_create_agenda_success(self, db_session, test_user, test_event):
        """Test successful agenda creation through service"""
        agenda_logic = AgendaLogic()
        agenda_data = AgendaCreate(title="Service Test Agenda", description="Test description")
        
        status, response = agenda_logic.create_agenda(db_session, test_event.id, test_user.id, agenda_data)
        
        assert status == 201
        assert response.agenda.title == "Service Test Agenda"
        assert response.agenda.description == "Test description"
    
    def test_create_agenda_duplicate(self, db_session, test_agenda, test_user, test_event):
        """Test agenda creation when one already exists"""
        agenda_logic = AgendaLogic()
        agenda_data = AgendaCreate(title="Duplicate Agenda")
        
        with pytest.raises(Exception) as exc_info:
            agenda_logic.create_agenda(db_session, test_event.id, test_user.id, agenda_data)
        
        assert "already exists" in str(exc_info.value)
    
    def test_create_agenda_item_success(self, db_session, test_agenda, test_user, test_event):
        """Test successful agenda item creation through service"""
        agenda_logic = AgendaLogic()
        item_data = AgendaItemCreate(
            title="Service Test Item",
            start_time=time(15, 0),
            type=APIAgendaItemType.SPEECH,
            is_important=True
        )
        
        status, response = agenda_logic.create_agenda_item(db_session, test_event.id, test_user.id, item_data)
        
        assert status == 201
        assert response.agenda_item.title == "Service Test Item"
        assert response.agenda_item.is_important is True
    
    def test_create_agenda_item_invalid_time(self, db_session, test_agenda, test_user, test_event):
        """Test agenda item creation with invalid time range"""
        agenda_logic = AgendaLogic()
        item_data = AgendaItemCreate(
            title="Invalid Time Item",
            start_time=time(18, 0),
            end_time=time(17, 0),  # End before start
            type=APIAgendaItemType.MEAL
        )
        
        with pytest.raises(Exception) as exc_info:
            agenda_logic.create_agenda_item(db_session, test_event.id, test_user.id, item_data)
        
        assert "End time must be after start time" in str(exc_info.value)
    
    def test_reorder_agenda_items_success(self, db_session, test_agenda_items, test_user, test_event):
        """Test successful agenda item reordering through service"""
        agenda_logic = AgendaLogic()
        
        reorder_data = AgendaReorderRequest(
            items=[
                ReorderItem(item_id=test_agenda_items[2].id, display_order=1),
                ReorderItem(item_id=test_agenda_items[0].id, display_order=2),
                ReorderItem(item_id=test_agenda_items[1].id, display_order=3)
            ]
        )
        
        status, response = agenda_logic.reorder_agenda_items(db_session, test_event.id, test_user.id, reorder_data)
        
        assert status == 200
        assert "successfully reordered" in response["detail"]


class TestCascadeDeletion:
    """Tests for cascade deletion behavior"""
    
    def test_event_deletion_cascades_to_agenda_and_items(self, db_session, test_user, test_event, test_agenda, test_agenda_items):
        """Test that deleting an event cascades to agenda and items"""
        event_query = EventQuery()
        agenda_query = AgendaQuery()
        agenda_item_query = AgendaItemQuery()
        
        # Verify everything exists before deletion
        assert event_query.get_one(db_session, test_event.id, test_user.id) is not None
        assert agenda_query.get_one(db_session, test_event.id, test_user.id) is not None
        assert len(agenda_item_query.get_all_for_agenda(db_session, test_event.id, test_user.id)) == 3
        
        # Delete the event
        result = event_query.delete(db_session, test_event.id, test_user.id)
        assert result is True
        
        # Verify cascade deletion
        assert event_query.get_one(db_session, test_event.id, test_user.id) is None
        assert agenda_query.get_one(db_session, test_event.id, test_user.id) is None
        assert len(agenda_item_query.get_all_for_agenda(db_session, test_event.id, test_user.id)) == 0
    
    def test_agenda_deletion_cascades_to_items(self, db_session, test_agenda, test_agenda_items, test_user, test_event):
        """Test that deleting an agenda cascades to items but not event"""
        event_query = EventQuery()
        agenda_query = AgendaQuery()
        agenda_item_query = AgendaItemQuery()
        
        # Delete the agenda
        result = agenda_query.delete(db_session, test_event.id, test_user.id)
        assert result is True
        
        # Verify agenda and items are deleted but event remains
        assert event_query.get_one(db_session, test_event.id, test_user.id) is not None
        assert agenda_query.get_one(db_session, test_event.id, test_user.id) is None
        assert len(agenda_item_query.get_all_for_agenda(db_session, test_event.id, test_user.id)) == 0


class TestErrorHandling:
    """Tests for error handling scenarios"""
    
    def test_agenda_operations_with_nonexistent_event(self, db_session, test_user):
        """Test agenda operations with nonexistent event"""
        agenda_query = AgendaQuery()
        fake_event_id = generate_event_id()
        
        # All operations should return None or False
        assert agenda_query.get_one(db_session, fake_event_id, test_user.id) is None
        assert agenda_query.create(db_session, fake_event_id, test_user.id, "Test") is None
        assert agenda_query.update(db_session, fake_event_id, test_user.id, "Test") is None
        assert agenda_query.delete(db_session, fake_event_id, test_user.id) is None
        assert agenda_query.validate_ownership(db_session, fake_event_id, test_user.id) is False
    
    def test_agenda_item_operations_with_nonexistent_agenda(self, db_session, test_user):
        """Test agenda item operations with nonexistent agenda"""
        agenda_item_query = AgendaItemQuery()
        fake_event_id = generate_event_id()
        fake_item_id = generate_agenda_item_id()
        
        item_data = {"title": "Test", "start_time": time(12, 0), "type": "other"}
        
        # All operations should return None or False
        assert agenda_item_query.get_one(db_session, fake_item_id, fake_event_id, test_user.id) is None
        assert agenda_item_query.get_all_for_agenda(db_session, fake_event_id, test_user.id) == []
        assert agenda_item_query.create(db_session, fake_event_id, test_user.id, item_data) is None
        assert agenda_item_query.update(db_session, fake_item_id, fake_event_id, test_user.id, item_data) is None
        assert agenda_item_query.delete(db_session, fake_item_id, fake_event_id, test_user.id) is None
        assert agenda_item_query.bulk_reorder(db_session, fake_event_id, test_user.id, []) is None
        assert agenda_item_query.validate_ownership(db_session, fake_item_id, fake_event_id, test_user.id) is False
    
    def test_unauthorized_access_scenarios(self, db_session, test_agenda, test_agenda_items, test_event):
        """Test various unauthorized access scenarios"""
        agenda_query = AgendaQuery()
        agenda_item_query = AgendaItemQuery()
        wrong_user_id = generate_user_id()
        
        # All operations should fail for wrong user
        assert agenda_query.get_one(db_session, test_event.id, wrong_user_id) is None
        assert agenda_query.create(db_session, test_event.id, wrong_user_id, "Test") is None
        assert agenda_query.update(db_session, test_event.id, wrong_user_id, "Test") is None
        assert agenda_query.delete(db_session, test_event.id, wrong_user_id) is None
        
        item = test_agenda_items[0]
        item_data = {"title": "Test"}
        
        assert agenda_item_query.get_one(db_session, item.id, test_event.id, wrong_user_id) is None
        assert agenda_item_query.get_all_for_agenda(db_session, test_event.id, wrong_user_id) == []
        assert agenda_item_query.create(db_session, test_event.id, wrong_user_id, item_data) is None
        assert agenda_item_query.update(db_session, item.id, test_event.id, wrong_user_id, item_data) is None
        assert agenda_item_query.delete(db_session, item.id, test_event.id, wrong_user_id) is None
        assert agenda_item_query.bulk_reorder(db_session, test_event.id, wrong_user_id, []) is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])