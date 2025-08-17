# Verwenden Sie ein Python-Basis-Image
FROM python:3.12-slim

# Setzen Sie das Arbeitsverzeichnis im Container
WORKDIR /app

# Kopieren Sie die Anwendungsdateien in das Arbeitsverzeichnis
COPY *.py /app/

# Installieren Sie die benötigten Python-Abhängigkeiten
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Geben Sie den Port an, den die Anwendung verwendet
EXPOSE 4500

# Startbefehl für die Anwendung
#CMD ["python", "main.py"]
CMD ["waitress-serve", "--listen=0.0.0.0:4500", "main:app"]