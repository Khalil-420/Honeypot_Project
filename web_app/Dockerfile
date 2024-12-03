# Use the official Python image as the base
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Install necessary dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Install Gunicorn (WSGI server)
RUN pip install gunicorn

# Copy the application code into the container
COPY . /app/

# Expose the port that the app will run on
EXPOSE 5000

# Command to run the application with Gunicorn
CMD ["gunicorn", "-w", "4", "app:app", "--bind", "0.0.0.0:5000"]
