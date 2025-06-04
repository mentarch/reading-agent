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
- **Article tracking to prevent duplicate processing and summaries**

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
- **Set tracking retention period for processed articles**

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

## Article Tracking

The application now keeps track of processed articles to avoid duplicate processing and summaries:

- Articles are identified by URL or a combination of title and source
- The tracking information is stored in `data/processed_articles.json`
- Old tracking records are automatically cleared after the retention period (default 30 days)

You can view tracked articles using the provided utility:

```bash
# Show the 10 most recently processed articles
python src/utils/show_tracked_articles.py

# Show up to 20 articles
python src/utils/show_tracked_articles.py --limit 20

# Filter by source
python src/utils/show_tracked_articles.py --source "arXiv"

# Output as JSON
python src/utils/show_tracked_articles.py --format json
```

## Running and Managing as a Service

The application comes with comprehensive management scripts to run it as a background service and manage its operation.

### Basic Service Management with `manage.sh`

```bash
# Make the script executable (first time only)
chmod +x manage.sh

# Start the service in the background
./manage.sh start

# Check if it's running and see basic stats
./manage.sh status

# View the most recent log entries
./manage.sh logs

# View only errors in the logs
./manage.sh logs errors

# View all tracked articles
./manage.sh tracked

# Stop the service
./manage.sh stop

# Restart the service
./manage.sh restart

# Run the test suite to verify functionality
./manage.sh test
```

### Maintenance with `maintenance.sh`

```bash
# Make the script executable (first time only)
chmod +x maintenance.sh

# Create a backup of all data
./maintenance.sh backup

# Clean up old backups and tracked articles
./maintenance.sh cleanup

# Clean up only old backups
./maintenance.sh cleanup backups

# Clean up only old articles
./maintenance.sh cleanup articles

# Repair the tracking database if corrupted
./maintenance.sh repair
```

### Monitoring with `monitor.sh`

```bash
# Make the script executable (first time only)
chmod +x monitor.sh

# Quick check of service health
./monitor.sh check

# Get a detailed status report
./monitor.sh detailed

# Check for issues and send alerts (if email configured)
./monitor.sh alerts
```

### Setting Up Automatic Monitoring

Add to your crontab (`crontab -e`):

```
# Check service every hour and send alerts if needed
0 * * * * /path/to/reading-agent/monitor.sh alerts

# Clean up old data weekly
0 0 * * 0 /path/to/reading-agent/maintenance.sh cleanup

# Create a backup daily
0 2 * * * /path/to/reading-agent/maintenance.sh backup
```

### Important Notes for Service Operation

1. The service requires the `PYTHONPATH` to be set for proper module imports, which the management scripts handle automatically.
2. For email alerts, update the `EMAIL` variable in `monitor.sh`.
3. The service creates a PID file (`.service.pid`) to track the running process.
4. Log files are stored in the `logs` directory.
5. Backups are stored in the `backups` directory.

## Recent Improvements

- **Management Scripts**: Added comprehensive scripts for running and monitoring as a service
- **Article Tracking**: Added tracking to prevent duplicate processing of the same articles
- **Enhanced Resilience**: Added retry mechanisms for OpenAI API calls and email sending
- **Robust Error Handling**: Improved error handling for external services
- **Proxy Handling**: Fixed issues with proxy configurations affecting the OpenAI client
- **Resource Optimization**: Limited the number of articles processed to reduce API usage
- **Better Fallbacks**: Added random summary generation when API summarization fails
- **Email Formatting**: Improved HTML email template for better readability

## Troubleshooting

If you encounter issues:

1. **Import Errors**: Always run with `PYTHONPATH=.` or use the management scripts which set this automatically
2. **Email Sending Problems**: Check your SMTP settings and credentials
3. **OpenAI API Errors**: Verify your API key and check for any proxy settings causing conflicts
4. **No Articles Found**: Check your configured sources - note that arXiv doesn't publish on weekends
5. **Service Not Starting**: Check the logs with `./manage.sh logs` for detailed error information
6. **Database Corruption**: Use `./maintenance.sh repair` to attempt recovery

## Source Availability

Some sources like arXiv have specific publication schedules:
- arXiv typically doesn't publish new articles on weekends (as indicated by `<skipDays>` in their RSS feed)
- If no articles are found, try enabling multiple sources or check on weekdays
