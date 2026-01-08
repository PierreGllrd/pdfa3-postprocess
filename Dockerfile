# Service de post-traitement PDF/A-3 avec Ghostscript
FROM python:3.11-slim

# Installer Ghostscript, ghostscript-x (apporte les profils ICC) et pip
RUN apt-get update && \
    apt-get install -y ghostscript ghostscript-x python3-pip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Installer PyPDF2 pour la détection des pages vides
RUN pip3 install --no-cache-dir PyPDF2

# Vérifier que Ghostscript est installé
RUN gs --version

# Copier le serveur et le fichier de configuration PDFA
COPY fix-pdfa3-server.py /app/fix-pdfa3-server.py
COPY PDFA_def.ps /app/PDFA_def.ps

# Exposer le port
EXPOSE 8080

# Démarrer le serveur
CMD ["python3", "/app/fix-pdfa3-server.py"]

