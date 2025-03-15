# Hello World Example App

This is a simple Flask application that serves as a test subject for the TestGen tool. It includes:
- Basic web interface
- REST API endpoints
- Unit tests
- Integration with frontend JavaScript

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
cd app
python app.py
```

The application will be available at http://localhost:5000

## Running Tests

To run the tests:
```bash
pytest tests/
```

## API Endpoints

- `GET /` - Home page with interactive UI
- `GET /api/hello` - Returns a hello world message
- `GET /api/greet/<name>` - Returns a personalized greeting

## Project Structure

```
hello_world/
├── app/
│   ├── app.py
│   └── templates/
│       └── index.html
├── tests/
│   └── test_app.py
├── requirements.txt
└── README.md
``` 