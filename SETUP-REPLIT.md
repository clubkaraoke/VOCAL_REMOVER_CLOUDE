# 🚀 Desplegar en Replit (GRATIS)

La web en GitHub Pages necesita un servidor. Aquí te muestro cómo usar Replit (es gratis).

## 📋 PASOS:

### 1. Ve a Replit
```
https://replit.com
```

### 2. Login (o crea cuenta)
- Click en "Sign Up"
- Usa GitHub para login fácil

### 3. Importa tu repo
- Click en "Create" → "Import from GitHub"
- Busca: `clubkaraoke/VOCAL_REMOVER_CLOUDE`
- Click en el repo

### 4. Espera a que configure
Replit va a leer:
- `replit.nix` (dependencias)
- `.replit` (cómo correr)
- `requirements.txt` (librerías Python)

### 5. Run
Click en botón "Run" (▶)

Espera ~30 segundos. Debería ver en el panel derecho:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 6. Obtén tu URL pública
En el panel derecho, copiar la URL que empieza con:
```
https://VOCAL_REMOVER_CLOUDE.clubkaraoke.replit.dev
```

(Algo así - la URL exacta varía)

### 7. Actualiza la web
En GitHub, edita: `docs/index.html`

Busca esta línea:
```javascript
const API_BASE = 'https://your-replit-url.replit.dev/api';
```

Reemplaza por tu URL de Replit:
```javascript
const API_BASE = 'https://VOCAL_REMOVER_CLOUDE.clubkaraoke.replit.dev/api';
```

Commit y push.

### 8. ¡LISTO!
Abre:
```
https://clubkaraoke.github.io/VOCAL_REMOVER_CLOUDE/
```

La web ahora conecta a tu servidor en Replit.

---

## 🎯 RESUMEN:

1. Replit.com
2. Import GitHub
3. Run
4. Copiar URL
5. Actualizar docs/index.html
6. Commit & Push
7. ¡LISTO!

---

## ⚠️ IMPORTANTE:

- Replit duerme si no usas por 1 hora (tier gratis)
- Para que NUNCA duerma, upgrade a Replit Pro ($7/mes)
- O mantén tu compu prendida corriendo el servidor local

---

## 📞 PROBLEMAS:

**Error: "Cannot connect"**
- Espera 5 minutos, Replit puede estar iniciando
- Recarga la página

**Error: "Module not found"**
- Replit está instalando dependencias, espera

**La URL es diferente**
- Cada usuario tiene su propia URL de Replit
- Cópiala exacta desde el panel

---

**¿Hiciste todo? Avísame la URL y te ayudo.** 🚀
