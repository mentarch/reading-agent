# Research Article Reader and Summarizer

This application automatically retrieves research articles from configured sources (RSS feeds or APIs) like PubMed and arXiv, filters them based on topics of interest (e.g., machine vision), summarizes their content using OpenAI, and emails the summaries to you.

## Features

- Retrieve articles from multiple sources (PubMed, arXiv, etc.)
- Filter articles based on user-defined topics
- Summarize article content using OpenAI with fallbacks for API failures
- Email regular digests with article summaries in HTML and plain text formats
- Configurable schedule for retrievals and emails
- Robust error handling and retry mechanisms for external services
- Optimized for running on Python 3.13

## Setup and Installation

1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure your sources and topics in `config.yaml`
4. Set up environment variables for email and OpenAI API in `.env`
5. Run the application: `python -m src.main`

## Configuration

Edit `config.yaml` to:
- Add data sources (PubMed, arXiv, etc.)
- Define topics of interest
- Configure email settings
- Set retrieval schedule
- Limit number of articles to process and include in emails
- Configure OpenAI model and summary length

## Environment Variables

Create a `.env` file with the following:
```
EMAIL_SENDER=your-email@example.com
EMAIL_PASSWORD=your-app-password
EMAIL_RECIPIENT=recipient@example.com
EMAIL_SMTP_SERVER=smtp.example.com
EMAIL_SMTP_PORT=587
OPENAI_API_KEY=your-openai-api-key
```

## Recent Improvements

- **Enhanced Resilience**: Added retry mechanisms for OpenAI API calls and email sending
- **Robust Error Handling**: Improved error handling for external services
- **Proxy Handling**: Fixed issues with proxy configurations affecting the OpenAI client
- **Resource Optimization**: Limited the number of articles processed to reduce API usage
- **Better Fallbacks**: Added random summary generation when API summarization fails
- **Email Formatting**: Improved HTML email template for better readability

## Troubleshooting

If you encounter issues:

1. **Email Sending Problems**: Check your SMTP settings and credentials
2. **OpenAI API Errors**: Verify your API key and check for any proxy settings causing conflicts
3. **Import Errors**: Run the application using `python -m src.main` to avoid import path issues
4. **No Articles Found**: Check your configured sources and topics in `config.yaml`

## Running as a Service

To run the application as a background service:

```bash
nohup python -m src.main > app.log 2>&1 &
```

This will keep the application running in the background and log output to `app.log`.