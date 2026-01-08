# 🔧 Nouvelle Correction pour OutputIntent RGB

## ✅ Changement principal

J'ai modifié la commande Ghostscript pour utiliser **`UseDeviceIndependentColor`** au lieu de **`RGB`**.

Cette option force Ghostscript à convertir toutes les couleurs DeviceRGB en couleurs indépendantes du périphérique, ce qui **oblige** Ghostscript à créer un OutputIntent RGB.

## 📝 Fichiers modifiés

1. **`fix-pdfa3-server.py`** :
   - Changé `-sColorConversionStrategy=RGB` → `-sColorConversionStrategy=UseDeviceIndependentColor`
   - Cette option est **cruciale** pour forcer l'OutputIntent

2. **`PDFA_def.ps`** :
   - Fichier de configuration amélioré pour définir l'OutputIntent sRGB
   - Définit l'OutputIntent avec l'identifiant sRGB IEC61966-2.1

3. **`Dockerfile`** :
   - Copie maintenant `PDFA_def.ps` dans l'image Docker

## 🚀 Prochaines étapes

1. **Pousser sur GitHub** :
   ```bash
   cd ../pdfa3-postprocess-temp
   git add fix-pdfa3-server.py PDFA_def.ps Dockerfile
   git commit -m "Fix OutputIntent RGB with UseDeviceIndependentColor"
   git push
   ```

2. **Attendre le redéploiement** sur Render.com (automatique)

3. **Tester** :
   - Générer une facture Factur-X
   - Valider le PDF avec un validateur PDF/A-3
   - L'erreur DeviceRGB devrait être corrigée !

## 🎯 Pourquoi ça devrait fonctionner

`UseDeviceIndependentColor` :
- Convertit DeviceRGB → CalRGB (couleurs indépendantes)
- **Force** Ghostscript à créer un OutputIntent RGB
- C'est la méthode recommandée pour PDF/A-3 strict

## ⚠️ Si ça ne fonctionne toujours pas

Vérifiez les logs Render.com pour voir si Ghostscript génère des erreurs ou des warnings. La commande devrait maintenant être correcte.


