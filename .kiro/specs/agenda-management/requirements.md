# Agenda Management Requirements

## Introduction

Implementacija sistema za upravljanje agendama događaja koji omogućava kreiranje, ažuriranje i organizovanje programa događaja sa detaljnim stavkama i mogućnostima reorder-a.

## Requirements

### Requirement 1

**User Story:** As an event organizer, I want to create an agenda for my event, so that guests can see the schedule and program of activities.

#### Acceptance Criteria

1. WHEN I create an agenda THEN the system SHALL store the agenda with title, description and event association
2. WHEN I create an agenda THEN the system SHALL generate a unique NanoID for the agenda
3. WHEN I create an agenda THEN the system SHALL set default title to "Program događaja" if not provided
4. WHEN I create an agenda THEN the system SHALL validate that I own the event
5. WHEN I create an agenda THEN the system SHALL return the created agenda with all details

### Requirement 2

**User Story:** As an event organizer, I want to add items to my event agenda, so that I can specify detailed schedule with times and activities.

#### Acceptance Criteria

1. WHEN I add an agenda item THEN the system SHALL store the item with title, description, start_time, end_time, location, type, display_order, and is_important flag
2. WHEN I add an agenda item THEN the system SHALL validate that the agenda exists and I own the event
3. WHEN I add an agenda item THEN the system SHALL support item types: ceremony, reception, entertainment, speech, meal, break, photo_session, other
4. WHEN I add an agenda item THEN the system SHALL automatically set display_order if not provided
5. WHEN I add an agenda item THEN the system SHALL validate time format (HH:MM)
6. WHEN I add an agenda item THEN the system SHALL allow marking items as important for highlighting

### Requirement 3

**User Story:** As an event organizer, I want to retrieve my event agenda, so that I can view the complete schedule and share it with guests.

#### Acceptance Criteria

1. WHEN I request an agenda THEN the system SHALL return the agenda with all associated items
2. WHEN I request an agenda THEN the system SHALL order items by display_order and start_time
3. WHEN I request an agenda THEN the system SHALL validate that I own the event
4. WHEN no agenda exists THEN the system SHALL return 404 status
5. WHEN I request an agenda THEN the system SHALL include all item details (title, times, location, type, importance)

### Requirement 4

**User Story:** As an event organizer, I want to update my agenda and its items, so that I can modify the schedule as needed.

#### Acceptance Criteria

1. WHEN I update an agenda THEN the system SHALL allow modifying title and description
2. WHEN I update an agenda item THEN the system SHALL allow modifying all item properties
3. WHEN I update an agenda or item THEN the system SHALL validate that I own the event
4. WHEN I update an agenda or item THEN the system SHALL update the updated_at timestamp
5. WHEN I update a non-existent agenda or item THEN the system SHALL return 404 status

### Requirement 5

**User Story:** As an event organizer, I want to delete agenda items or the entire agenda, so that I can remove outdated or incorrect information.

#### Acceptance Criteria

1. WHEN I delete an agenda THEN the system SHALL remove the agenda and all associated items
2. WHEN I delete an agenda item THEN the system SHALL remove only that specific item
3. WHEN I delete an agenda or item THEN the system SHALL validate that I own the event
4. WHEN I delete a non-existent agenda or item THEN the system SHALL return 404 status
5. WHEN I delete an agenda or item THEN the system SHALL return 204 status on success

### Requirement 6

**User Story:** As an event organizer, I want to reorder agenda items, so that I can organize the schedule in the correct sequence.

#### Acceptance Criteria

1. WHEN I reorder agenda items THEN the system SHALL accept an array of item_id and order pairs
2. WHEN I reorder agenda items THEN the system SHALL update the display_order for each specified item
3. WHEN I reorder agenda items THEN the system SHALL validate that all items belong to the agenda
4. WHEN I reorder agenda items THEN the system SHALL validate that I own the event
5. WHEN I reorder agenda items THEN the system SHALL return success status after reordering

### Requirement 7

**User Story:** As a system, I want to maintain proper relationships between events, agendas, and agenda items, so that data integrity is preserved.

#### Acceptance Criteria

1. WHEN an agenda is created THEN the system SHALL establish a foreign key relationship to the event
2. WHEN agenda items are created THEN the system SHALL establish a foreign key relationship to the agenda
3. WHEN an event is deleted THEN the system SHALL cascade delete associated agendas and items
4. WHEN an agenda is deleted THEN the system SHALL cascade delete associated items
5. WHEN validating ownership THEN the system SHALL check through the event-agenda-item relationship chain