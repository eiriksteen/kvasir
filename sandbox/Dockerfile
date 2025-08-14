FROM python:3.11-slim

WORKDIR /app

# Copy the data_structures package first
COPY data_structures ./data_structures

# Install the data_structures package
RUN pip install --upgrade pip && \
    pip install -e ./data_structures

# Copy the sandbox package
COPY sandbox .

# Install the sandbox package
RUN pip install -e .

# Command to run when container starts
CMD ["tail", "-f", "/dev/null"]
