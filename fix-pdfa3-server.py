#!/usr/bin/env python3
"""
Serveur HTTP simple pour post-traiter les PDFs avec Ghostscript
Écoute sur le port configuré via PORT (défaut 8080)
"""

import os
import sys
import subprocess
import tempfile
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = int(os.environ.get('PORT', 8080))

class PDFA3Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_error(404)
    
    def do_POST(self):
        if self.path != '/fix-pdfa3':
            self.send_error(404)
            return
        
        content_length = int(self.headers.get('Content-Length', 0))
        pdf_data = self.rfile.read(content_length)
        
        if len(pdf_data) == 0:
            self.send_error(400, "No PDF data received")
            return
        
        # Créer des fichiers temporaires
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as input_file:
            input_file.write(pdf_data)
            input_path = input_file.name
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as output_file:
            output_path = output_file.name
        
        try:
            # Post-traiter avec Ghostscript - COMMANDE AMÉLIORÉE pour PDF/A-3 strict
            # Ces options forcent Ghostscript à générer l'OutputIntent RGB et l'ID keyword
            print(f"Processing PDF: {len(pdf_data)} bytes", flush=True)
            
            # Chemin vers le fichier de configuration PDFA (si disponible)
            pdfa_def_path = '/app/PDFA_def.ps'
            if not os.path.exists(pdfa_def_path):
                pdfa_def_path = None
            
            # Construire la commande Ghostscript
            # Utiliser UseDeviceIndependentColor pour forcer la création d'un OutputIntent
            gs_command = [
                'gs',
                '-dPDFA=3',                                    # PDF/A-3
                '-dBATCH',                                     # Pas d'interaction
                '-dNOPAUSE',                                   # Pas de pause
                '-dNOOUTERSAVE',                               # Pas de sauvegarde externe
                '-sColorConversionStrategy=UseDeviceIndependentColor', # Utiliser couleurs indépendantes (FORCE OutputIntent)
                '-sOutputFile=' + output_path,
                '-sDEVICE=pdfwrite',                           # Device de sortie PDF
                '-dPDFACompatibilityPolicy=1',                 # Politique de compatibilité PDF/A stricte
                '-dUseCIEColor=true',                          # Utiliser les couleurs CIE (OBLIGATOIRE pour OutputIntent)
                '-dCompatibilityLevel=1.4',                    # Compatibilité PDF 1.4 (minimum pour PDF/A-3)
                '-sProcessColorModel=DeviceRGB',               # Modèle de couleur RGB
                '-dPDFSETTINGS=/prepress',                     # Paramètres prépresse (FORCE l'ID keyword dans le trailer)
                '-dEmbedAllFonts=true',                        # Embarquer toutes les polices
                '-dSubsetFonts=true',                          # Sous-ensembler les polices (optimisation)
                '-dAutoRotatePages=/None',                     # Pas de rotation automatique
            ]
            
            # Ajouter le fichier de configuration PDFA si disponible
            if pdfa_def_path:
                gs_command.append(pdfa_def_path)
            
            # Ajouter le fichier PDF d'entrée
            gs_command.append(input_path)
            
            result = subprocess.run(gs_command, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0 and os.path.exists(output_path):
                output_size = os.path.getsize(output_path)
                print(f"Ghostscript success: output size {output_size} bytes", flush=True)
                
                # Lire le PDF corrigé
                with open(output_path, 'rb') as f:
                    corrected_pdf = f.read()
                
                # Vérifier que le PDF a une taille raisonnable
                if len(corrected_pdf) < 100:
                    print(f"Warning: PDF output too small ({len(corrected_pdf)} bytes)", flush=True)
                    self.send_error(500, "Ghostscript output too small")
                    return
                
                # Envoyer le PDF corrigé
                self.send_response(200)
                self.send_header('Content-Type', 'application/pdf')
                self.send_header('Content-Length', str(len(corrected_pdf)))
                self.end_headers()
                self.wfile.write(corrected_pdf)
            else:
                error_msg = result.stderr if result.stderr else "Unknown error"
                print(f"Ghostscript error (code {result.returncode}): {error_msg}", flush=True)
                self.send_error(500, f"Ghostscript failed: {error_msg}")
        except subprocess.TimeoutExpired:
            self.send_error(504, "Ghostscript timeout")
        except Exception as e:
            self.send_error(500, str(e))
        finally:
            # Nettoyer les fichiers temporaires
            try:
                os.unlink(input_path)
                if os.path.exists(output_path):
                    os.unlink(output_path)
            except:
                pass
    
    def log_message(self, format, *args):
        # Logger les requêtes importantes
        print(f"{self.address_string()} - {format % args}", flush=True)

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', PORT), PDFA3Handler)
    print(f'PDF/A-3 post-process server listening on port {PORT}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nShutting down...', flush=True)
        server.shutdown()

