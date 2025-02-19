# Use an official Python runtime as a base image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /chatops  

# Copy the requirements file and install dependencies
COPY requirements.txt .  
RUN pip install -r requirements.txt  

# Copy the rest of the application code
COPY . .  

# Expose the port your app runs on
EXPOSE 5000  

# Set the command to run the application
#CMD ["python3 -m flask -A /app.py run --host=0.0.0.0"]
CMD ["python3", "-m", "flask", "--app", "project/app.py", "run", "--host=0.0.0.0"]