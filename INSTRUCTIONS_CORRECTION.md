# 🔧 Instructions de Correction - Service PDF/A-3

## ✅ Ce qui a été corrigé

J'ai déjà modifié `fix-pdfa3-server.py` avec une **commande Ghostscript améliorée** qui devrait corriger les erreurs PDF/A-3.

## 📝 Ce qu'il reste à faire

### 1. Vérifier que le fichier est bien modifié

Le fichier `fix-pdfa3-server.py` devrait maintenant avoir une commande Ghostscript avec ces options importantes :
- `-dPDFSETTINGS=/prepress` → Force l'ID keyword dans le trailer
- `-dUseCIEColor=true` → Permet de créer un OutputIntent RGB
- `-dCompatibilityLevel=1.4` → PDF 1.4 minimum pour PDF/A-3

### 2. Pousser sur GitHub et redéployer

```bash
cd ../pdfa3-postprocess-temp

# Vérifier les modifications
git status

# Ajouter les fichiers modifiés
git add fix-pdfa3-server.py

# Committer
git commit -m "Improve Ghostscript command for PDF/A-3 strict compliance"

# Pousser
git push
```

### 3. Redéployer sur Render.com

Render.com devrait redéployer automatiquement. Sinon, allez dans Render.com → votre service → Manual Deploy.

### 4. Tester

1. Tester avec : `https://votre-site.com/api/test-fix-pdfa3.php`
2. Générer une facture Factur-X
3. Valider le PDF avec un validateur PDF/A-3 externe

## ⚠️ Si ça ne fonctionne toujours pas

Vérifiez les logs Render.com pour voir les erreurs Ghostscript. Les logs affichent maintenant :
- "Processing PDF: X bytes"
- "Ghostscript success: output size X bytes" ou les erreurs

## 🎯 Résultat attendu

Après redéploiement, les 2 erreurs PDF/A-3 devraient être corrigées :
- ✅ OutputIntent RGB présent (corrige DeviceRGB)
- ✅ ID keyword présent (corrige l'erreur ID keyword)


