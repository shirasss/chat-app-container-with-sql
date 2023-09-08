# Use an official Python runtime as a parent image
FROM python:3.8

ENV FLASK_ENV development

# Set the working directory in the container
WORKDIR /code

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install dependencies
RUN pip install -r requirements.txt

# Set the timezone (optional)
ENV TZ 'Israel'

# Set environment variables
ENV DATA_DIR='./data/'
ENV ROOMS_DIR=${DATA_DIR}'rooms/'

# Copy the content of the local src directory to the working directory
COPY . .

# Command to run on container start
CMD ["python", "./server.py"]
