# Alert System

A containerized application that handles user authentication, SMS alerts, and email follow-ups. The system allows users to create time-sensitive alerts that require responses within a specified timeframe. If no response is received, the system automatically sends follow-up emails.

## Features

- User authentication (login/register)
- SMS alert creation with customizable messages
- Response deadline tracking
- Automatic email follow-ups for missed deadlines
- Containerized deployment using Docker

## Prerequisites

- Docker
- Twilio account for SMS functionality
- Email account for sending follow-up emails (Gmail recommended)

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```
# Flask configuration
SECRET_KEY=your-secret-key-here

# Twilio configuration
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_PHONE_NUMBER=your-twilio-phone-number

# Email configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-specific-password
```

## Setup and Running

1. Clone the repository
2. Create and configure the `.env` file as shown above
3. Build and run the Docker container:

```bash
docker build -t alert-system .
docker run -p 5000:5000 --env-file .env alert-system
```

4. Access the application at `http://localhost:5000`

## Usage

1. Register an account with your email and phone number
2. Log in to access the dashboard
3. Create new alerts with custom messages and response deadlines
4. Respond to alerts before the deadline to prevent email follow-ups
5. View all your alerts and their status in the dashboard

## Security Notes

- Never commit the `.env` file to version control
- Use strong passwords and keep your API keys secure
- For Gmail, use App-Specific Passwords instead of your account password

## Technical Stack

- Python 3.9
- Flask web framework
- SQLAlchemy for database management
- Twilio for SMS functionality
- SMTP for email notifications
- Bootstrap 5 for frontend styling
- Docker for containerization 