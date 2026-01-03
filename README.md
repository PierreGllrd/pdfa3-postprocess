# Service de Post-traitement PDF/A-3

Service séparé pour post-traiter les PDFs avec Ghostscript et corriger les erreurs PDF/A-3.

## Déploiement sur Render.com

### Option 1 : Via GitHub

1. **Créer un repo GitHub** avec ce dossier
2. **Sur Render.com** :
   - New + → Web Service
   - Connecter GitHub → Sélectionner le repo
   - **Name** : `pdfa3-postprocess` (ou autre)
   - **Region** : Même que Gotenberg
   - **Branch** : `main`
   - **Root Directory** : Laissez vide ou `gotenberg-postprocess`
   - **Build Command** : Laissez vide (Dockerfile)
   - **Start Command** : Laissez vide
   - **Plan** : Free (gratuit)

3. **Notez l'URL** : Render vous donnera une URL comme `https://pdfa3-postprocess-xxxx.onrender.com`

### Option 2 : Via Docker Hub

1. Build et push l'image :
```bash
cd gotenberg-postprocess
docker build -t votre-username/pdfa3-postprocess:latest .
docker push votre-username/pdfa3-postprocess:latest
```

2. **Sur Render.com** :
   - New + → Web Service
   - **Environment** : Docker
   - **Docker Image URL** : `docker.io/votre-username/pdfa3-postprocess:latest`

## Configuration dans le code PHP

Une fois déployé, mettez à jour `utils/GotenbergClient.php` avec l'URL du nouveau service :

```php
// Dans postProcessWithGhostscript()
$postProcessUrl = 'https://pdfa3-postprocess-xxxx.onrender.com';
```

Ou mieux, ajoutez dans `.env` :
```env
PDFA3_POSTPROCESS_URL=https://pdfa3-postprocess-xxxx.onrender.com
```

