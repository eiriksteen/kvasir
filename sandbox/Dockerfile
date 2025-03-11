FROM python:3.11-slim

WORKDIR /app

# Copy the entire project
COPY . .

# Install the package
RUN pip install .

# Command to run when container starts

CMD ["tail", "-f", "/dev/null"]
