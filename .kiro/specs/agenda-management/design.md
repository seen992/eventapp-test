# Agenda Management Design

## Overview

Agenda management sistem omogućava kreiranje i upravljanje programom događaja kroz hijerarhijsku strukturu: Event -> Agenda -> AgendaItem. Sistem koristi NanoID identifikatore i podržava CRUD operacije sa validacijom vlasništva.

## Architecture

### Database Schema

```sql
-- Agenda table
CREATE TABLE agendas (
    id VARCHAR(12) PRIMARY KEY,
    event_id VARCHAR(12) NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL DEFAULT 'Program događaja',
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Agenda items table  
CREATE TABLE agenda_items (
    id VARCHAR(12) PRIMARY KEY,
    agenda_id VARCHAR(12) NOT NULL REFERENCES agendas(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    start_time TIME NOT NULL,
    end_time TIME,
    location VARCHAR(200),
    type VARCHAR(50) NOT NULL CHECK (type IN ('ceremony', 'reception', 'entertainment', 'speech', 'meal', 'break', 'photo_session', 'other')),
    display_order INTEGER DEFAULT 0,
    is_important BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_agendas_event_id ON agendas(event_id);
CREATE INDEX idx_agenda_items_agenda_id ON agenda_items(agenda_id);
CREATE INDEX idx_agenda_items_display_order ON agenda_items(agenda_id, display_order, start_time);
```

### API Endpoints

1. **GET /events/{event_id}/agenda**
   - Returns agenda with ordered items
   - 404 if agenda doesn't exist
   - Validates event ownership

2. **POST /events/{event_id}/agenda**
   - Creates new agenda for event
   - Validates event exists and user owns it
   - Returns created agenda

3. **PUT /events/{event_id}/agenda**
   - Updates existing agenda
   - Validates ownership
   - Updates only title and description

4. **DELETE /events/{event_id}/agenda**
   - Deletes agenda and all items (cascade)
   - Validates ownership
   - Returns 204 on success

5. **POST /events/{event_id}/agenda/items**
   - Adds new item to agenda
   - Validates agenda exists and ownership
   - Auto-assigns display_order if not provided

6. **PUT /events/{event_id}/agenda/items/{item_id}**
   - Updates specific agenda item
   - Validates item belongs to agenda and ownership

7. **DELETE /events/{event_id}/agenda/items/{item_id}**
   - Deletes specific agenda item
   - Validates ownership

8. **PUT /events/{event_id}/agenda/reorder**
   - Bulk updates display_order for items
   - Validates all items belong to agenda

## Components and Interfaces

### Models

#### Database Models (SQLAlchemy)
```python
class Agenda(Base):
    __tablename__ = "agendas"
    
    id = Column(String(12), primary_key=True, default=generate_agenda_id)
    event_id = Column(String(12), ForeignKey('events.id'), nullable=False)
    title = Column(String(200), nullable=False, default='Program događaja')
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=datetime.now(UTC), onupdate=datetime.now(UTC))
    
    # Relationships
    event = relationship("Event", back_populates="agenda")
    items = relationship("AgendaItem", back_populates="agenda", cascade="all, delete-orphan", order_by="AgendaItem.display_order, AgendaItem.start_time")

class AgendaItem(Base):
    __tablename__ = "agenda_items"
    
    id = Column(String(12), primary_key=True, default=generate_agenda_item_id)
    agenda_id = Column(String(12), ForeignKey('agendas.id'), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time)
    location = Column(String(200))
    type = Column(Enum('ceremony', 'reception', 'entertainment', 'speech', 'meal', 'break', 'photo_session', 'other', name='agenda_item_type'), nullable=False)
    display_order = Column(Integer, default=0)
    is_important = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=datetime.now(UTC), onupdate=datetime.now(UTC))
    
    # Relationships
    agenda = relationship("Agenda", back_populates="items")
```

#### API Models (Pydantic)
```python
class AgendaItemCreate(BaseModel):
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    start_time: time
    end_time: Optional[time] = None
    location: Optional[str] = Field(None, max_length=200)
    type: str = Field(..., pattern="^(ceremony|reception|entertainment|speech|meal|break|photo_session|other)$")
    display_order: Optional[int] = 0
    is_important: Optional[bool] = False

class AgendaCreate(BaseModel):
    title: Optional[str] = Field("Program događaja", max_length=200)
    description: Optional[str] = None
    items: Optional[List[AgendaItemCreate]] = []

class AgendaResponse(BaseModel):
    id: str
    event_id: str
    title: str
    description: Optional[str]
    items: List[AgendaItemResponse]
    created_at: datetime
    updated_at: datetime
```

### Services

#### AgendaLogic
- Handles business logic for agenda operations
- Validates ownership through event relationship
- Manages agenda and item CRUD operations
- Handles reordering logic

#### AgendaQuery (DAO)
- Database access layer for agendas
- Implements CRUD operations
- Handles complex queries with joins
- Manages cascading operations

## Data Models

### Agenda Entity
- **id**: NanoID (12 chars) - Primary key
- **event_id**: Foreign key to events table
- **title**: Agenda title (default: "Program događaja")
- **description**: Optional detailed description
- **items**: One-to-many relationship with AgendaItem
- **timestamps**: created_at, updated_at

### AgendaItem Entity
- **id**: NanoID (12 chars) - Primary key
- **agenda_id**: Foreign key to agendas table
- **title**: Item title (required)
- **description**: Optional item description
- **start_time**: Required start time (TIME format)
- **end_time**: Optional end time
- **location**: Optional location
- **type**: Enum of item types
- **display_order**: Integer for custom ordering
- **is_important**: Boolean flag for highlighting
- **timestamps**: created_at, updated_at

## Error Handling

### Validation Errors
- 400: Invalid input data (malformed times, invalid types)
- 400: Missing required fields
- 400: Invalid enum values

### Authorization Errors
- 401: Invalid or missing authentication
- 403: User doesn't own the event

### Not Found Errors
- 404: Event not found
- 404: Agenda not found
- 404: Agenda item not found

### Business Logic Errors
- 409: Agenda already exists for event (if implementing single agenda per event)
- 422: Invalid time ranges (end_time before start_time)

## Testing Strategy

### Unit Tests
- Model validation tests
- Service logic tests
- DAO operation tests
- Error handling tests

### Integration Tests
- Full API endpoint tests
- Database relationship tests
- Cascade deletion tests
- Ownership validation tests

### Test Data
- Create test events with known owners
- Create test agendas with various configurations
- Test edge cases (empty agendas, complex reordering)
- Test authorization scenarios

### Performance Tests
- Large agenda with many items
- Concurrent agenda modifications
- Reordering performance with many items