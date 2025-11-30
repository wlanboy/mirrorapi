FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py /app/

EXPOSE 4500

#CMD ["python", "main.py"]
CMD ["waitress-serve", "--listen=0.0.0.0:4500", "main:app"]