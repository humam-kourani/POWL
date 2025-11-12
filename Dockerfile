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
RUN pip install --upgrade pip
RUN apt install -y graphviz
RUN pip install uv
WORKDIR /app
# Install the Python dependencies using uv
COPY . .
RUN pip install .
RUN uv lock

# Expose the port 8501 for Streamlit
EXPOSE 8501

# Command to run the Streamlit app
CMD ["uv", "run", "streamlit", "run", "app.py"]
