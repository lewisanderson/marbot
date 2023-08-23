# Use the official Python 3 image as the base image
FROM python:3

# Set the working directory inside the container
WORKDIR /app

# Copy the local requirements.txt file to the container
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

COPY scripts /app/scripts

# By default, run python3 interpreter (you can change this to your specific script if needed)
CMD ["python3"]
