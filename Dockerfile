FROM python:3.12-slim
WORKDIR /chatops
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python3", "-m", "flask", "--app", "project/app.py", "run", "--host=0.0.0.0"]
