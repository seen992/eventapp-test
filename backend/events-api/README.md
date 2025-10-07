# Events API

Simple FastAPI service for managing events with automatic database initialization.

## Features

- **Automatic Database Setup**: Creates database, schema, and tables automatically on startup
- **Health Check**: `/health-check` endpoint with database connectivity verification
- **User Management**: Create and manage users
- **Event Management**: CRUD operations for events
- **Single Database**: Uses one shared database instead of per-user databases

## Quick Start

### 1. Environment Setup

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` with your database credentials:
```bash
POSTGRES_DB_HOST=localhost
POSTGRES_DB_PORT=5432
POSTGRES_DB_USER=postgres
POSTGRES_DB_PASSWORD=your_password
POSTGRES_DB_NAME=eventsdb
POSTGRES_DB_SCHEMA=public
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the API

```bash
./run_server.sh
```

The API will:
- Automatically create the database if it doesn't exist
- Create the schema if it doesn't exist  
- Create all tables if they don't exist
- Start the server on port 8080

### 4. Test Database Initialization

```bash
python3 test_db_init.py
```

### 5. Test the API

```bash
curl http://localhost:8080/health-check
```

## API Endpoints

### System Endpoints

#### `GET /health-check`
Health check with database connectivity verification
```json
Response: {"HEALTH": "OK", "database": "connected"}
```

#### `DELETE /recreate-tables?recreate=true`
Recreate all database tables and enum types (destructive operation)
```json
Response: {"detail": "Tables recreated successfully"}
```

### User Management

#### `POST /users`
Create a new user
```json
{
  "email": "user@example.com",
  "name": "John Doe"
}
```

#### `GET /users/profile`
Get user profile (requires Authorization header)
```json
Response: {"id": "user_id", "email": "user@example.com", "name": "John Doe"}
```

#### `PUT /users/profile`
Update user profile (requires Authorization header)
```json
{
  "email": "newemail@example.com",
  "name": "Jane Doe"
}
```

### Event Management

#### `GET /events`
Get user's events with optional filtering (requires Authorization header)
Query parameters: `status` (active/expired/draft), `limit` (1-1000), `offset`
```json
Response: {"events": [...], "total": 10, "limit": 20, "offset": 0}
```

#### `POST /events`
Create new event (requires Authorization header)
```json
{
  "title": "My Event",
  "description": "Event description",
  "start_time": "2024-12-01T10:00:00Z",
  "end_time": "2024-12-01T18:00:00Z",
  "location": "Conference Center",
  "status": "draft"
}
```

#### `GET /events/{event_id}`
Get specific event (requires Authorization header)
```json
Response: {"id": "event_id", "title": "My Event", "description": "...", ...}
```

#### `PUT /events/{event_id}`
Update event (requires Authorization header)
```json
{
  "title": "Updated Event Title",
  "description": "Updated description",
  "status": "active"
}
```

#### `DELETE /events/{event_id}`
Delete event (requires Authorization header)
```json
Response: {"detail": "Event deleted successfully"}
```

### Agenda Management

#### `GET /events/{event_id}/agenda`
Get agenda for an event with all items ordered by display_order and start_time
```json
Response: {"id": "agenda_id", "event_id": "event_id", "items": [...]}
```

#### `POST /events/{event_id}/agenda`
Create a new agenda for an event
```json
{
  "title": "Event Agenda",
  "description": "Main agenda for the event"
}
```

#### `PUT /events/{event_id}/agenda`
Update an existing agenda for an event
```json
{
  "title": "Updated Agenda Title",
  "description": "Updated agenda description"
}
```

#### `DELETE /events/{event_id}/agenda`
Delete an agenda and all its items (cascade delete)
```json
Response: 204 No Content
```

### Agenda Items Management

#### `POST /events/{event_id}/agenda/items`
Create a new agenda item for an event's agenda
```json
{
  "title": "Opening Keynote",
  "description": "Welcome and introduction",
  "start_time": "2024-12-01T09:00:00Z",
  "end_time": "2024-12-01T10:00:00Z",
  "speaker": "John Speaker",
  "location": "Main Hall",
  "display_order": 1
}
```

#### `PUT /events/{event_id}/agenda/items/{item_id}`
Update an existing agenda item
```json
{
  "title": "Updated Keynote Title",
  "speaker": "Jane Speaker",
  "display_order": 2
}
```

#### `DELETE /events/{event_id}/agenda/items/{item_id}`
Delete a specific agenda item
```json
Response: 204 No Content
```

#### `PUT /events/{event_id}/agenda/reorder`
Reorder agenda items by updating their display_order values
```json
{
  "item_orders": [
    {"item_id": "item1", "display_order": 1},
    {"item_id": "item2", "display_order": 2}
  ]
}
```

## Authentication

The API uses a simple Bearer token system for testing. Include the user UUID in the Authorization header:

```bash
curl -H "Authorization: Bearer your-user-uuid" http://localhost:8080/events
```

## Docker

```bash
docker build -t events-api .
docker run -p 8080:8080 -e POSTGRES_DB_HOST=host.docker.internal events-api
```