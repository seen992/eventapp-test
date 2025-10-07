FROM python:3.13-slim

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV PYTHONUNBUFFERED=1

WORKDIR /opt/test-deploy-api

# Install dependencies
ADD requirements.txt ./
RUN echo ">>> Installing requirements..." && \
    pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Add application code
ADD app ./app
ADD run_server.sh ./

# Fix line endings and make executable
RUN sed -i 's/\r$//' run_server.sh && \
    chmod +x run_server.sh

# Expose port
EXPOSE 8080

# Use the run_server.sh script
CMD ["./run_server.sh"]