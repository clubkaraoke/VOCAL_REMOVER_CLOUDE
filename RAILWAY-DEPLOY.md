# 🚀 Railway Deploy - AUTOMÁTICO

Railway es un servicio que despliega tu app AUTOMÁTICAMENTE desde GitHub.

## 📋 PASO 1: Haz CLIC AQUÍ (es solo 1 click):

```
https://railway.app/new?repo=clubkaraoke/VOCAL_REMOVER_CLOUDE
```

Esto va a:
1. ✅ Abrir Railway
2. ✅ Detectar tu repo automáticamente
3. ✅ Deployar el código
4. ✅ Darte una URL pública

## 📝 PASO 2: Login en Railway

- Si no tienes cuenta, crea una (es gratis, 2 segundos)
- Usa GitHub para login = más fácil

## ✅ PASO 3: Confirma

Click en botones:
- "Connect Repository" 
- "Deploy Now"

Espera ~2 minutos. Railway va a:
1. Leer tu `Procfile`
2. Instalar `requirements.txt`
3. Correr tu API
4. **Darte una URL como:**
   ```
   https://vocal-remover-cloude-xxxx.railway.app
   ```

## 🔗 PASO 4: Obtén tu URL

En el panel de Railway, verás tu URL. Cópiala.

Debería verse así:
```
https://vocal-remover-cloude-xxxx.railway.app
```

## 🌐 PASO 5: Actualiza la web

En GitHub, ve a: `docs/index.html`

Busca esta línea (está cerca del inicio):
```javascript
const API_BASE = 'https://your-replit-url.replit.dev/api';
```

Reemplaza por tu URL de Railway:
```javascript
const API_BASE = 'https://vocal-remover-cloude-xxxx.railway.app/api';
```

(Usa la URL exacta que Railway te dio)

Commit y Push.

## 🎉 PASO 6: ¡LISTO!

Abre:
```
https://clubkaraoke.github.io/VOCAL_REMOVER_CLOUDE/
```

La web ahora conecta a tu API en Railway.

---

## ⚠️ IMPORTANTE:

- **Railway es GRATIS** el primer mes
- Después cuesta ~$5/mes para que esté siempre prendido
- Sin pagar, se apaga después de inactividad (pero vuelve al recargar)

---

## 🆘 SI ALGO FALLA:

**Error: "Cannot find module"**
- Railway está instalando, espera 2 minutos

**Error: "Connection refused"**
- Verifica que la URL sea correcta en docs/index.html
- Recarga la página

**URL no funciona**
- Espera a que Railway termine de deployar (panel verde = listo)

---

## 📞 RESUMEN:

1. Click en link Railway arriba
2. Login con GitHub
3. Click "Deploy Now"
4. Espera 2 minutos
5. Copia URL de Railway
6. Edita docs/index.html
7. Commit & Push
8. ¡FUNCIONA!

---

**¿Lista? Haz clic en el link de Railway arriba y listo.** 🚀
