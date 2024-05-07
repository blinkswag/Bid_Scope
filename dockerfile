FROM python:3.9-slim-buster

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host=files.pythonhosted.org -r requirements.txt

COPY . .


# Expose port
EXPOSE 5000

# Define default command to run the Flask application
CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]
