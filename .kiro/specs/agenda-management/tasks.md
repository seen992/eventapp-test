# Agenda Management Implementation Plan

- [x] 1. Create database models and relationships
  - Create Agenda and AgendaItem SQLAlchemy models with proper relationships
  - Add foreign key constraints and cascade delete behavior
  - Create enum type for agenda item types
  - Add relationship to Event model for agenda
  - _Requirements: 1.1, 1.2, 7.1, 7.2, 7.3, 7.4_

- [x] 2. Create NanoID generators for agenda entities
  - Add generate_agenda_id and generate_agenda_item_id functions to nanoid utility
  - Ensure 12-character length consistency with existing ID generators
  - _Requirements: 1.2_

- [x] 3. Create Pydantic API models for agenda operations
  - Implement AgendaCreate, AgendaUpdate, AgendaItemCreate, AgendaItemUpdate models
  - Add proper validation for time formats, string lengths, and enum values
  - Create response models AgendaResponse and AgendaItemResponse
  - Add reorder request model for bulk display_order updates
  - _Requirements: 2.3, 2.5, 2.6, 6.1_

- [x] 4. Implement agenda database access layer (DAO)
  - Create AgendaQuery class with CRUD operations for agendas
  - Create AgendaItemQuery class with CRUD operations for agenda items
  - Implement get_agenda_with_items method that returns agenda with ordered items
  - Add ownership validation methods that check through event relationship
  - Implement bulk reorder method for updating display_order values
  - _Requirements: 3.2, 4.2, 4.3, 5.1, 5.2, 6.2, 7.5_

- [x] 5. Create agenda business logic service layer
  - Implement AgendaLogic class with methods for all agenda operations
  - Add event ownership validation for all operations
  - Implement auto-assignment of display_order for new items
  - Add validation for agenda existence and item relationships
  - Handle error cases and return appropriate HTTP status codes
  - _Requirements: 1.4, 2.2, 2.4, 3.3, 4.3, 5.3, 6.3_

- [x] 6. Implement agenda API endpoints
  - Create GET /events/{event_id}/agenda endpoint with item ordering
  - Create POST /events/{event_id}/agenda endpoint with validation
  - Create PUT /events/{event_id}/agenda endpoint for updates
  - Create DELETE /events/{event_id}/agenda endpoint with cascade behavior
  - Add proper error handling and status codes for all endpoints
  - _Requirements: 1.5, 3.1, 3.4, 4.4, 4.5, 5.4, 5.5_

- [x] 7. Implement agenda item API endpoints
  - Create POST /events/{event_id}/agenda/items endpoint for adding items
  - Create PUT /events/{event_id}/agenda/items/{item_id} endpoint for updates
  - Create DELETE /events/{event_id}/agenda/items/{item_id} endpoint
  - Add validation for item types and time formats
  - Ensure proper ownership validation through agenda-event relationship
  - _Requirements: 2.1, 2.2, 2.3, 2.5, 4.1, 4.2, 5.1, 5.2_

- [x] 8. Implement agenda reordering functionality
  - Create PUT /events/{event_id}/agenda/reorder endpoint
  - Validate that all item_ids belong to the specified agenda
  - Implement bulk update of display_order values
  - Add transaction handling for atomic reordering operations
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 9. Add agenda relationship to Event model
  - Update Event model to include agenda relationship
  - Ensure proper cascade delete behavior when event is deleted
  - Update Event response models to optionally include agenda data
  - _Requirements: 7.1, 7.3_
