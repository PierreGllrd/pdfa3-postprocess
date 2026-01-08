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
from http.server import HTTPServer, BaseHTTPRequestHandler

try:
    import PyPDF2
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False
    print("Warning: PyPDF2 not available, empty page detection disabled", flush=True)

PORT = int(os.environ.get('PORT', 8080))

def detect_empty_pages(pdf_path):
    """
    Détecte les pages vides dans un PDF.
    Une page est considérée comme vide si elle ne contient pas de texte significatif
    et a très peu de contenu (typiquement causé par des marges qui créent une page supplémentaire).
    Retourne une liste des numéros de pages vides (0-indexed).
    """
    if not HAS_PYPDF2:
        return []
    
    empty_pages = []
    try:
        with open(pdf_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            total_pages = len(pdf_reader.pages)
            
            for page_num in range(total_pages):
                page = pdf_reader.pages[page_num]
                is_empty = False
                
                # Méthode 1: Vérifier le texte extrait
                text = page.extract_text()
                text_content = text.strip() if text else ""
                
                # Méthode 2: Vérifier le contenu de la page via le dictionnaire
                try:
                    page_dict = page.get_object()
                    content_size = 0
                    
                    # Vérifier la présence et la taille du contenu
                    if '/Contents' in page_dict:
                        contents = page_dict['/Contents']
                        # Si Contents est une liste d'objets, calculer la taille totale
                        if hasattr(contents, '__len__'):
                            if isinstance(contents, list):
                                # Si c'est une liste d'objets indirects, estimer la taille
                                content_size = len(contents)
                            else:
                                # Si c'est un objet unique, vérifier s'il est petit
                                content_size = 1
                    else:
                        # Pas de contenu du tout
                        content_size = 0
                    
                    # Une page est considérée vide si:
                    # 1. Pas de texte significatif (moins de 10 caractères)
                    # 2. ET très peu de contenu (moins de 2 objets de contenu)
                    if len(text_content) < 10 and content_size < 2:
                        is_empty = True
                        
                except Exception as e:
                    # Si on ne peut pas analyser le contenu, se baser uniquement sur le texte
                    if len(text_content) < 10:
                        is_empty = True
                
                if is_empty:
                    empty_pages.append(page_num)
        
        if empty_pages:
            print(f"Detected {len(empty_pages)} empty page(s): {[p+1 for p in empty_pages]}", flush=True)
        return empty_pages
    except Exception as e:
        print(f"Error detecting empty pages: {e}", flush=True)
        return []

def remove_empty_pages_with_gs(input_path, output_path, empty_pages):
    """
    Supprime les pages vides d'un PDF en utilisant PyPDF2.
    empty_pages: liste des numéros de pages à supprimer (0-indexed)
    """
    if not empty_pages:
        # Pas de pages à supprimer, copier le fichier tel quel
        import shutil
        shutil.copy2(input_path, output_path)
        return True
    
    if not HAS_PYPDF2:
        # Si PyPDF2 n'est pas disponible, on ne peut pas supprimer les pages
        print("Warning: PyPDF2 not available, cannot remove empty pages", flush=True)
        import shutil
        shutil.copy2(input_path, output_path)
        return False
    
    try:
        # Utiliser PyPDF2 pour créer un nouveau PDF sans les pages vides
        pdf_writer = PyPDF2.PdfWriter()
        with open(input_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            total_pages = len(pdf_reader.pages)
            
            for i in range(total_pages):
                if i not in empty_pages:
                    pdf_writer.add_page(pdf_reader.pages[i])
        
        if len(pdf_writer.pages) == 0:
            print("Error: All pages would be removed!", flush=True)
            return False
        
        # Écrire le PDF sans les pages vides
        with open(output_path, 'wb') as f:
            pdf_writer.write(f)
        
        print(f"Removed {len(empty_pages)} empty page(s), kept {len(pdf_writer.pages)} page(s)", flush=True)
        return True
    except Exception as e:
        print(f"Error removing empty pages: {e}", flush=True)
        # En cas d'erreur, copier le fichier original
        import shutil
        shutil.copy2(input_path, output_path)
        return False

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
        
        temp_cleaned_path = None  # Pour stocker le chemin du PDF nettoyé des pages vides
        
        try:
            # Post-traiter avec Ghostscript - COMMANDE AMÉLIORÉE pour PDF/A-3 strict
            # Ces options forcent Ghostscript à générer l'OutputIntent RGB et l'ID keyword
            print(f"Processing PDF: {len(pdf_data)} bytes", flush=True)
            
            # Étape 1: Détecter et supprimer les pages vides (causées par les marges Gotenberg)
            empty_pages = detect_empty_pages(input_path)
            if empty_pages:
                print(f"Removing {len(empty_pages)} empty page(s) before PDF/A-3 processing", flush=True)
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                    temp_cleaned_path = temp_file.name
                
                if remove_empty_pages_with_gs(input_path, temp_cleaned_path, empty_pages):
                    # Remplacer le fichier d'entrée par celui sans pages vides
                    os.unlink(input_path)
                    input_path = temp_cleaned_path
                    temp_cleaned_path = None  # Ne pas supprimer maintenant, on le fera dans finally
                else:
                    print("Warning: Failed to remove empty pages, continuing with original PDF", flush=True)
                    try:
                        os.unlink(temp_cleaned_path)
                        temp_cleaned_path = None
                    except:
                        pass
            
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
                if temp_cleaned_path and os.path.exists(temp_cleaned_path):
                    os.unlink(temp_cleaned_path)
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

