# 🔧 Restauration et Amélioration - Service PDF/A-3

## ✅ Ce qui a été fait

1. **Restauration de la version qui fonctionnait** :
   - Retour à `-sColorConversionStrategy=RGB` (au lieu de UseDeviceIndependentColor qui cassait l'ID keyword)
   - Conservation de `-dPDFSETTINGS=/prepress` qui génère l'ID keyword

2. **Amélioration du PDFA_def.ps** :
   - Utilisation de la syntaxe PostScript correcte avec `pdfmark`
   - Définition de l'OutputIntent sRGB IEC61966-2.1

3. **Installation de ghostscript-x** :
   - Ajout de `ghostscript-x` au Dockerfile
   - Apporte les profils ICC nécessaires pour l'OutputIntent

## 📝 Fichiers modifiés

1. **`fix-pdfa3-server.py`** :
   - Retour à la commande Ghostscript qui fonctionnait pour l'ID keyword
   - Utilisation de `-sColorConversionStrategy=RGB` (pas UseDeviceIndependentColor)
   - Conservation de toutes les options importantes

2. **`PDFA_def.ps`** :
   - Syntaxe PostScript correcte avec `pdfmark`
   - Définit l'OutputIntent sRGB IEC61966-2.1

3. **`Dockerfile`** :
   - Installation de `ghostscript-x` pour avoir les profils ICC

## 🚀 Prochaines étapes

1. **Pousser sur GitHub** :
   ```bash
   cd ../pdfa3-postprocess-temp
   git add fix-pdfa3-server.py PDFA_def.ps Dockerfile
   git commit -m "Restore working ID keyword + add OutputIntent support"
   git push
   ```

2. **Attendre le redéploiement** sur Render.com (automatique)

3. **Tester** :
   - Générer une facture Factur-X
   - Valider le PDF avec un validateur PDF/A-3
   - Les 2 erreurs devraient être corrigées :
     - ✅ ID keyword (restauré)
     - ✅ OutputIntent RGB (avec ghostscript-x + PDFA_def.ps)

## 🎯 Pourquoi ça devrait fonctionner maintenant

- **ID keyword** : `-dPDFSETTINGS=/prepress` force Ghostscript à générer l'ID (version qui fonctionnait)
- **OutputIntent** : `ghostscript-x` apporte les profils ICC, et `PDFA_def.ps` définit l'OutputIntent avec la bonne syntaxe

## ⚠️ Si ça ne fonctionne toujours pas

Vérifiez les logs Render.com pour voir si :
- Ghostscript trouve le fichier PDFA_def.ps
- Il y a des erreurs sur l'OutputIntent
- Le profil ICC est bien disponible


