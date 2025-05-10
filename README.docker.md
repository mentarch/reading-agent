# Dockerized Research Article Reader

This guide explains how to run the Research Article Reader and Summarizer using Docker.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/) (included with Docker Desktop)

## Quick Start

1. Clone this repository
2. Create a `.env` file with your configuration (see below)
3. Run the application:

```bash
docker-compose up -d
```

## Environment Variables

Create a `.env` file in the same directory as docker-compose.yml with these required variables:

```
EMAIL_SENDER=your-email@example.com
EMAIL_PASSWORD=your-app-password
EMAIL_RECIPIENT=recipient@example.com
EMAIL_SMTP_SERVER=smtp.example.com
EMAIL_SMTP_PORT=587
OPENAI_API_KEY=your-openai-api-key
```

## Configuration

The `config.yaml` file is mounted as a volume, so you can edit it without rebuilding the Docker image:

1. Edit `config.yaml` to configure your sources, topics, and application settings
2. If you change the configuration while the container is running, restart it:

```bash
docker-compose restart
```

## Data Persistence

The application uses three volume mounts for data persistence:

- `./data:/app/data` - Stores processed articles and tracking information
- `./logs:/app/logs` - Contains application logs
- `./backups:/app/backups` - Stores backups created by the maintenance script

## Managing the Service

You can use standard Docker commands to manage the application:

```bash
# View logs
docker-compose logs -f

# Stop the service
docker-compose down

# Restart the service
docker-compose restart

# Update to the latest version (after pulling from Git)
docker-compose build --pull
docker-compose up -d
```

## Running One-Off Commands

To run maintenance tasks or view tracked articles:

```bash
# View tracked articles
docker exec reading-agent python src/utils/show_tracked_articles.py

# Create a backup
docker exec reading-agent ./maintenance.sh backup

# Clean up old data
docker exec reading-agent ./maintenance.sh cleanup
```

## Troubleshooting

If you encounter issues:

1. Check the logs: `docker-compose logs -f`
2. Verify your environment variables in the `.env` file
3. Ensure the `config.yaml` file is properly configured
4. Check that the required volumes (data, logs, backups) are writable 