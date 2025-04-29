# PITC Technical Task

## Project Overview
This project implements a digital platform for managing customer orders, account managers, and service providers. The platform includes comprehensive statistical analysis capabilities and reporting features.

## Features
- Customer and Order Management
- Account Manager Dashboard
- Service Provider Integration
- Statistical Analysis and Reporting
- Campaign Performance Tracking
- Job Execution Monitoring

## Technical Stack
- Python 3.8+
- Django 4.2+
- Django REST Framework
- PostgreSQL

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd [repository-name]
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Apply database migrations:
```bash
python manage.py migrate
```

5. Create a superuser:
```bash
python manage.py createsuperuser
```

6. Load demo data (optional):
```bash
python manage.py setup_demo
```

7. Run the development server:
```bash
python manage.py runserver
```

## Project Structure
- `execution/` - Core application for order and job management
  - `models.py` - Database models for orders, jobs, customers, etc.
  - `views.py` - API views and viewsets
  - `admin.py` - Django admin interface customization
  
- `stat_analysis/` - Statistical analysis application
  - `models.py` - Models for reports and statistics
  - `stat_utils.py` - Statistical calculation utilities
  
## API Documentation
The API documentation is available at `/api/docs/` when running the development server.

## Testing
Run the test suite:
```bash
python manage.py test
```

## License
MIT License

## Authors
Created as part of the technical task for TU/e – PITC 