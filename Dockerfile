FROM python:3.11-slim

# Install Node.js
RUN apt-get update && apt-get install -y \
    curl \
    gnupg2 \
    lsb-release \
    ca-certificates && \
    curl -fsSL https://deb.nodesource.com/setup_16.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean

RUN pip install uv

# Install the Python dependencies using uv
COPY pyproject.toml poetry.lock /app/
RUN uv install --no-dev


# Set the working directory
WORKDIR /app

# Copy the application code into the container
COPY . /app

# Expose the port Streamlit runs on (8080)
EXPOSE 8080

# Command to run the Streamlit app
CMD ["uv", "run", "streamlit", "run", "app.py"]
