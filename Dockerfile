FROM python:3.12-slim

# Install Node.js (required by Hexo)
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g hexo-cli && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -e ".[ui,llm]"

EXPOSE 8501

VOLUME ["/app/config.json", "/blog"]

CMD ["streamlit", "run", "notion_to_hexo/app.py", "--server.headless", "true", "--server.port", "8501"]
