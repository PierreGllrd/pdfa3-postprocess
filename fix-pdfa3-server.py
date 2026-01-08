#!/usr/bin/env python3
"""
Serveur HTTP simple pour post-traiter les PDFs avec Ghostscript
Écoute sur le port configuré via PORT (défaut 8080)
"""

import os
import sys
import subprocess
import tempfile
import glob
import io
from http.server import HTTPServer, BaseHTTPRequestHandler
try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    # Fallback pour anciennes versions
    try:
        from PyPDF2 import PdfReader, PdfWriter
    except ImportError:
        PdfReader = None
        PdfWriter = None

PORT = int(os.environ.get('PORT', 8080))

def remove_empty_pages(pdf_data):
    """
    Détecte et supprime les pages vides d'un PDF.
    Retourne le PDF modifié ou None si pypdf n'est pas disponible.
    """
    if PdfReader is None:
        print("Warning: pypdf not available, skipping empty page removal", flush=True)
        return pdf_data
    
    try:
        pdf_reader = PdfReader(io.BytesIO(pdf_data))
        pdf_writer = PdfWriter()
        pages_removed = 0
        
        for page_num, page in enumerate(pdf_reader.pages):
            # Extraire le texte de la page
            text = page.extract_text().strip()
            
            # Vérifier si la page contient du contenu
            # Une page est considérée vide si :
            # 1. Pas de texte (ou seulement des espaces)
            # 2. Pas d'images (on pourrait aussi vérifier les images mais c'est plus complexe)
            if len(text) == 0:
                print(f"Page {page_num + 1} is empty, removing it", flush=True)
                pages_removed += 1
                continue
            
            # Garder la page
            pdf_writer.add_page(page)
        
        if pages_removed > 0:
            print(f"Removed {pages_removed} empty page(s)", flush=True)
            # Écrire le PDF modifié dans un buffer
            output_buffer = io.BytesIO()
            pdf_writer.write(output_buffer)
            return output_buffer.getvalue()
        else:
            print("No empty pages found", flush=True)
            return pdf_data
    
    except Exception as e:
        print(f"Error removing empty pages: {e}, keeping original PDF", flush=True)
        return pdf_data

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
            
            # Chercher un profil ICC sRGB système (avec ghostscript-x installé)
            possible_icc_paths = [
                '/usr/share/color/icc/sRGB.icc',
                '/usr/share/color/icc/ghostscript/srgb.icc',
                '/usr/local/share/ghostscript/*/iccprofiles/srgb.icc',
                '/usr/share/ghostscript/*/iccprofiles/srgb.icc',
            ]
            
            icc_profile = None
            for pattern in possible_icc_paths:
                if '*' in pattern:
                    # Utiliser glob pour chercher
                    import glob
                    matches = glob.glob(pattern)
                    if matches:
                        icc_profile = matches[0]
                        break
                elif os.path.exists(pattern):
                    icc_profile = pattern
                    break
            
            # Si pas de profil ICC trouvé, essayer de trouver via gs
            if not icc_profile:
                try:
                    result_gs = subprocess.run(['gs', '--help'], capture_output=True, text=True, timeout=5)
                    # Chercher dans le chemin standard de Ghostscript
                    import glob
                    gs_icc_paths = glob.glob('/usr/share/ghostscript/*/iccprofiles/*.icc')
                    if gs_icc_paths:
                        # Prendre le premier profil RGB trouvé
                        for path in gs_icc_paths:
                            if 'srgb' in path.lower() or 'rgb' in path.lower():
                                icc_profile = path
                                break
                except:
                    pass
            
            if icc_profile:
                print(f"Found ICC profile: {icc_profile}", flush=True)
            else:
                print("Warning: No ICC profile found, using PDFA_def.ps", flush=True)
            
            # Construire la commande Ghostscript
            # Utiliser UseDeviceIndependentColor pour forcer OutputIntent, mais avec -dPDFSETTINGS pour l'ID
            # AMÉLIORATIONS pour le rendu des traits (résolution et antialiasing)
            gs_command = [
                'gs',
                '-dPDFA=3',                                    # PDF/A-3
                '-dBATCH',                                     # Pas d'interaction
                '-dNOPAUSE',                                   # Pas de pause
                '-dNOOUTERSAVE',                               # Pas de sauvegarde externe
                '-sColorConversionStrategy=UseDeviceIndependentColor', # Force OutputIntent (convertit DeviceRGB)
                '-sOutputFile=' + output_path,
                '-sDEVICE=pdfwrite',                           # Device de sortie PDF
                '-dPDFACompatibilityPolicy=1',                 # Politique de compatibilité PDF/A stricte
                '-dUseCIEColor=true',                          # Utiliser les couleurs CIE (OBLIGATOIRE pour OutputIntent)
                '-dCompatibilityLevel=1.4',                    # Compatibilité PDF 1.4 (minimum pour PDF/A-3)
                '-dPDFSETTINGS=/prepress',                     # Paramètres prépresse (FORCE l'ID keyword)
                '-dEmbedAllFonts=true',                        # Embarquer toutes les polices
                '-dSubsetFonts=true',                          # Sous-ensembler les polices
                '-dAutoRotatePages=/None',                     # Pas de rotation automatique
                # Améliorations pour le rendu des traits (problème Mac)
                '-dResolution=300',                            # Résolution élevée pour meilleur rendu
                '-dTextAlphaBits=4',                           # Antialiasing texte 4 bits (meilleure qualité)
                '-dGraphicsAlphaBits=4',                       # Antialiasing graphiques 4 bits
                '-dRenderTextAsOutlines=false',                # Garder le texte comme texte (pas en contours)
                '-dPreserveHalftoneInfo=true',                 # Préserver les informations de tramage
            ]
            
            # Ajouter le profil ICC si trouvé
            if icc_profile:
                gs_command.extend([
                    '-sOutputICCProfile=' + icc_profile,       # Profil ICC pour OutputIntent
                    '--permit-file-read=' + icc_profile,       # Autoriser la lecture du profil
                ])
            else:
                # Fallback: utiliser PDFA_def.ps si pas de profil ICC
                pdfa_def_path = '/app/PDFA_def.ps'
                if os.path.exists(pdfa_def_path):
                    gs_command.append(pdfa_def_path)
            
            # Ajouter le fichier PDF d'entrée en dernier
            gs_command.append(input_path)
            
            print(f"Ghostscript command: {' '.join(gs_command)}", flush=True)
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
                
                # Supprimer les pages vides
                corrected_pdf = remove_empty_pages(corrected_pdf)
                
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

