# Base image with Python
FROM python:3.12-alpine

# Set working directory
WORKDIR /app

# Copy server code
COPY . .

#Remove client code
RUN rm -rf src/client
RUN rm -rf src/main.py

# Install from requirements.txt
# Install dependencies

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN rm -rf requirements.txt


# Set environment variables
ENV MCP_SERVER_HOST=0.0.0.0
ENV MCP_SERVER_PORT=8000
ENV OLLAMA_HOST=http://localhost:11434
ENV MCP_SERVER_OLLAMA_MODEL=llama3.1:latest
ENV MCP_SERVER_TRANSPORT=sse
ENV LOG_LEVEL=INFO

# Create a directory inside the container
RUN mkdir -p /app/allowed-path
ENV ALLOWED_PATHS='/app/allowed-path'

# Expose port
EXPOSE ${MCP_SERVER_PORT}

# Start the MCP server
CMD ["python", "src/server_main.py"]
