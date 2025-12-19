FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY backfill/ ./backfill/

# Set environment variables (override at runtime)
ENV LOG_LEVEL=INFO
ENV GSHEET_NAME="Product Hunt Rankings"
ENV GSHEET_TAB="Weekly Top 10"

# Default command: run weekly scraper
CMD ["python", "-m", "src.main"]
