# NeoFi Event Management System

A collaborative event management API built with FastAPI, PostgreSQL, and Alembic. Features include user authentication, event versioning, role-based permissions, and real-time collaboration.

---

## Database Schema Overview

### User
| Field         | Type      | Description                |
|--------------|-----------|----------------------------|
| id           | int       | Primary key                |
| email        | str       | Unique email address       |
| username     | str       | Unique username            |
| hashed_password | str    | Hashed password            |
| is_active    | bool      | User is active             |
| created_at   | datetime  | Creation timestamp         |
| updated_at   | datetime  | Last update timestamp      |

### Event
| Field         | Type      | Description                |
|--------------|-----------|----------------------------|
| id           | int       | Primary key                |
| title        | str       | Event title                |
| description  | str       | Event description          |
| start_time   | datetime  | Start time                 |
| end_time     | datetime  | End time                   |
| location     | str       | Location (optional)        |
| is_recurring | bool      | Is recurring event         |
| recurrence_pattern | dict | Recurrence details         |
| owner_id     | int       | User who owns the event    |
| created_at   | datetime  | Creation timestamp         |
| updated_at   | datetime  | Last update timestamp      |

### EventPermission
| Field         | Type      | Description                |
|--------------|-----------|----------------------------|
| id           | int       | Primary key                |
| event_id     | int       | Linked event               |
| user_id      | int       | Linked user                |
| role         | enum      | owner/editor/viewer        |
| created_at   | datetime  | Creation timestamp         |
| updated_at   | datetime  | Last update timestamp      |

### EventVersion
| Field         | Type      | Description                |
|--------------|-----------|----------------------------|
| id           | int       | Primary key                |
| event_id     | int       | Linked event               |
| version_number | int     | Version number             |
| data         | dict      | Event data at this version |
| created_by   | int       | User who made the version  |
| created_at   | datetime  | Creation timestamp         |
| change_description | str | Description of change      |

### EventChangeLog
| Field         | Type      | Description                |
|--------------|-----------|----------------------------|
| id           | int       | Primary key                |
| event_id     | int       | Linked event               |
| version_id   | int       | Linked version             |
| field_name   | str       | Field changed              |
| old_value    | any       | Old value                  |
| new_value    | any       | New value                  |
| created_by   | int       | User who made the change   |
| created_at   | datetime  | Change timestamp           |

---

## API Endpoints

All endpoints are prefixed with `/api/v1`.

### Authentication
| Method | Path                  | Description                  |
|--------|----------------------|------------------------------|
| POST   | /auth/register       | Register a new user          |
| POST   | /auth/login          | Login and get JWT token      |
| POST   | /auth/refresh        | Refresh JWT token            |
| POST   | /auth/logout         | Logout (client-side only)    |

### Event Management
| Method | Path                        | Description                                 |
|--------|-----------------------------|---------------------------------------------|
| POST   | /events                     | Create a new event                          |
| GET    | /events                     | List all events accessible to the user      |
| GET    | /events/{event_id}          | Get a specific event                        |
| PUT    | /events/{event_id}          | Update an event                             |
| DELETE | /events/{event_id}          | Delete an event                             |

### Collaboration & Permissions
| Method | Path                                         | Description                        |
|--------|----------------------------------------------|------------------------------------|
| POST   | /events/{event_id}/share                     | Share event with another user      |
| GET    | /events/{event_id}/permissions               | List all permissions for an event  |
| PUT    | /events/{event_id}/permissions/{user_id}     | Update a user's permission         |
| DELETE | /events/{event_id}/permissions/{user_id}     | Remove a user's access             |

### Versioning & Changelog
| Method | Path                                                        | Description                        |
|--------|-------------------------------------------------------------|------------------------------------|
| GET    | /events/{event_id}/history/{version_number}                 | Get a specific version of an event |
| POST   | /events/{event_id}/rollback/{version_number}                | Rollback to a previous version     |
| GET    | /events/{event_id}/changelog                                | Get the changelog for an event     |
| GET    | /events/{event_id}/diff/{version_number1}/{version_number2} | Get diff between two versions      |

---

## Quickstart
1. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up your `.env` file (see `.env.example` for variables).
4. Initialize the database:
   ```bash
   alembic upgrade head
   ```
5. Run the app:
   ```bash
   uvicorn app.main:app --reload
   ```

API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

## Project Structure
- `app/` - Main application
- `alembic/` - Database migrations
- `tests/` - Test suite

## Testing
Run all tests:
```bash
pytest
```

## Contributing
Pull requests welcome. For major changes, open an issue first.