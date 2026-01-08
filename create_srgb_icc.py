#!/usr/bin/env python3
"""
Script pour créer un profil ICC sRGB minimal si nécessaire
"""

# Ce script pourrait être utilisé pour créer un profil ICC minimal
# Pour l'instant, on essaie de trouver un profil système

import os

# Les chemins possibles pour les profils ICC sRGB
ICC_PATHS = [
    '/usr/share/color/icc/sRGB.icc',
    '/usr/share/color/icc/ghostscript/srgb.icc',
    '/usr/local/share/ghostscript/*/iccprofiles/srgb.icc',
    '/usr/share/ghostscript/*/iccprofiles/srgb.icc',
]

def find_srgb_icc():
    import glob
    for pattern in ICC_PATHS:
        if '*' in pattern:
            matches = glob.glob(pattern)
            if matches:
                return matches[0]
        elif os.path.exists(pattern):
            return pattern
    return None

if __name__ == '__main__':
    icc = find_srgb_icc()
    if icc:
        print(icc)
    else:
        print("No ICC profile found")


