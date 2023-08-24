FROM jupyter/scipy-notebook

# Set the working directory inside the container
WORKDIR /app

# Copy the local requirements.txt file to the container
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# By default, run python3 interpreter (you can change this to your specific script if needed)
# CMD ["python3"]
