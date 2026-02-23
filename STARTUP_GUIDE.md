# Secure AI Studio - Startup Guide

## Quick Start

To run the Secure AI Studio application, follow these steps:

### 1. Environment Setup
```bash
# Navigate to project directory
cd c:/Users/Rafael Feltrim/Documents/secure-ai-studio

# Activate virtual environment (if using one)
# venv\Scripts\activate

# Install dependencies (if not already installed)
pip install -r requirements.txt
```

### 2. Configuration
Create a `.env` file based on `.env.example` and add your API keys:

```bash
# Copy the example file
copy .env.example .env

# Edit the .env file to add your actual API keys
```

Required environment variables:
- `REPLICATE_API_TOKEN` - Your Replicate API token
- `FLASK_SECRET_KEY` - A secure secret key for Flask sessions

### 3. Run the Application
```bash
# Option 1: Using the startup script
python start_app.py

# Option 2: Direct execution
python app/main.py

# Option 3: For development with auto-reload
flask run --host=0.0.0.0 --port=5000
```

### 4. Access the Application
- Open your browser to: `http://localhost:5000`
- The API endpoints are available at the same address

## Verification Steps

After starting the application, verify the following:

1. **Homepage loads**: Visit `http://localhost:5000`
2. **API endpoints respond**: Test `/api/budget-status`
3. **Security features active**: Check that rate limiting works
4. **Logging works**: Check the logs directory for activity

## Running Tests

To verify all functionality is working:

```bash
# Run all tests
python run_all_tests.py

# Run specific test suites
python -m pytest tests/unit/ -v
python -m pytest tests/test_security_utils.py -v
```

## Troubleshooting

### Common Issues:

1. **Port already in use**: Change the PORT environment variable
2. **Missing dependencies**: Run `pip install -r requirements.txt`
3. **API errors**: Verify your Replicate API token is correct
4. **Permission errors**: Run as administrator if needed

### Health Checks:

```bash
# Check budget status
curl http://localhost:5000/api/budget-status

# Test generation endpoint (with valid data)
curl -X POST http://localhost:5000/api/generate \
  -H "Content-Type: application/json" \
  -d "{\"prompt\":\"test\",\"type\":\"image\",\"consent\":true}"
```

## Production Deployment

For production use:
- Use HTTPS
- Set `FLASK_ENV=production`
- Configure proper logging
- Set up monitoring
- Use a production WSGI server like Gunicorn

## Security Features Active

✅ Prompt injection prevention  
✅ Rate limiting (5 requests/minute)  
✅ Budget controls ($5 limit with 92%/99% thresholds)  
✅ LGPD compliance with consent management  
✅ Data retention policy enforcement  
✅ API key validation  

The application is now ready for use!