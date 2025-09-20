# Events API

Events Management Platform API - MVP Faza 1

## Opis

API servis za upravljanje događajima sa QR kod sistemom. Omogućava korisnicima kreiranje i upravljanje događajima.

## Struktura

```
events-api/
├── app/
│   ├── api/
│   │   ├── models.py      # Pydantic modeli
│   │   ├── services.py    # Business logika
│   │   └── security.py    # Auth sistem
│   ├── database/
│   │   ├── models.py      # SQLAlchemy modeli
│   │   ├── daos.py        # Data Access Objects
│   │   └── db.py          # Database konfiguracija
│   ├── routers/
│   │   └── routes.py      # API rute
│   ├── utils/
│   │   ├── config.py      # Konfiguracija
│   │   ├── logger.py      # Logging
│   │   └── utils.py       # Utility funkcije
│   └── main.py            # FastAPI aplikacija
├── tests/
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── run_server.sh
```

## API Endpoints

### Users
- `POST /users` - Kreiranje novog korisnika
- `GET /users/profile` - Dohvatanje profila korisnika
- `PUT /users/profile` - Ažuriranje profila korisnika

### Events
- `GET /events` - Dohvatanje svih događaja korisnika
- `POST /events` - Kreiranje novog događaja
- `GET /events/{event_id}` - Dohvatanje detalja događaja
- `PUT /events/{event_id}` - Ažuriranje događaja
- `DELETE /events/{event_id}` - Brisanje događaja

### Utility
- `GET /health-check` - Health check
- `DELETE /recreate-tables` - Rekreiranje tabela (development)

## Autentifikacija

API koristi fake auth sistem za development:
- Authorization header: `Bearer <user_uuid>`
- user_uuid mora biti validan UUID
- Korisnik mora postojati u bazi podataka

## Pokretanje

### Lokalno
```bash
# Kreiranje virtual environment
python3 -m venv venv
source venv/bin/activate

# Instaliranje dependencies
pip install -r requirements.txt

# Pokretanje servera
./run_server.sh
```

### Docker
```bash
# Pokretanje sa Docker Compose
docker-compose up --build
```

## Database

- PostgreSQL
- Svaki korisnik ima svoju bazu podataka
- Automatsko kreiranje baze i tabela
- Foreign key relacija između events i users tabela

## Modeli

### User
- id (UUID, primary key)
- email (unique)
- first_name
- last_name
- phone
- created_at
- updated_at

### Event
- id (UUID, primary key)
- name
- plan (freemium, starter, plus, full)
- location
- restaurant_name
- date
- time
- event_type (wedding, birthday, baptism, graduation, anniversary, corporate, other)
- expected_guests
- description
- qr_code_url
- landing_page_url
- photo_count
- guest_count
- status (active, expired, draft)
- expires_at
- created_at
- updated_at
- owner_id (UUID, foreign key to users.id)

## Port

API se pokreće na portu 8081.
