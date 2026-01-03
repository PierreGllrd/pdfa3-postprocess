# 🔧 Correction Finale - Service PDF/A-3

## ✅ Changements majeurs

J'ai modifié `fix-pdfa3-server.py` pour :

1. **Chercher automatiquement un profil ICC sRGB système** :
   - Cherche dans les chemins standards où `ghostscript-x` installe les profils ICC
   - Utilise `-sOutputICCProfile` pour spécifier le profil ICC réel
   - Utilise `--permit-file-read` pour autoriser Ghostscript à lire le profil

2. **Utiliser `UseDeviceIndependentColor` + `-dPDFSETTINGS=/prepress`** :
   - `UseDeviceIndependentColor` force la conversion DeviceRGB → couleurs indépendantes
   - Cela OBLIGE Ghostscript à créer un OutputIntent RGB
   - `-dPDFSETTINGS=/prepress` devrait maintenir l'ID keyword

## 📝 Fichiers modifiés

- **`fix-pdfa3-server.py`** :
  - Recherche automatique d'un profil ICC sRGB
  - Utilisation de `-sOutputICCProfile` avec le profil trouvé
  - Logs améliorés pour debug

## 🚀 Prochaines étapes

1. **Pousser sur GitHub** :
   ```bash
   cd ../pdfa3-postprocess-temp
   git add fix-pdfa3-server.py
   git commit -m "Use real ICC profile for OutputIntent RGB"
   git push
   ```

2. **Attendre le redéploiement** sur Render.com

3. **Tester** :
   - Générer une facture Factur-X
   - Vérifier les logs Render.com pour voir si un profil ICC est trouvé
   - Valider le PDF avec un validateur PDF/A-3

## 🎯 Pourquoi ça devrait fonctionner

- **OutputIntent** : `-sOutputICCProfile` avec un vrai profil ICC + `UseDeviceIndependentColor` devrait créer un OutputIntent RGB valide
- **ID keyword** : `-dPDFSETTINGS=/prepress` devrait le générer

## ⚠️ Si ça ne fonctionne toujours pas

Vérifiez les logs Render.com :
- Y a-t-il un message "Found ICC profile: ..." ?
- Y a-t-il des erreurs Ghostscript ?
- Le profil ICC est-il bien lu ?

Si aucun profil ICC n'est trouvé, on devra peut-être :
- Télécharger un profil sRGB.icc et l'inclure dans le Docker
- Ou utiliser une autre méthode pour créer l'OutputIntent

