# Use an official Python 3.11 slim image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file (already in the same folder as Dockerfile)
COPY /requirements.txt /app/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all the application files from the current folder
COPY . /app

# Expose the default Streamlit port
EXPOSE 8501

# Healthcheck to ensure the app is running
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Command to run the Streamlit app
CMD ["sh", "-c", "streamlit run energy_transition_chatbot_main.py --server.port=${PORT:-8501} --server.enableCORS=false"]

