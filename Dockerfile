# Service de post-traitement PDF/A-3 avec Ghostscript
FROM python:3.11-slim

# Installer Ghostscript
RUN apt-get update && \
    apt-get install -y ghostscript && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Vérifier que Ghostscript est installé
RUN gs --version

# Copier le serveur
COPY fix-pdfa3-server.py /app/fix-pdfa3-server.py

# Exposer le port
EXPOSE 8080

# Démarrer le serveur
CMD ["python3", "/app/fix-pdfa3-server.py"]

