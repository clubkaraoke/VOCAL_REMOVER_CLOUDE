# 🎵 Audio DAW - GitHub Pages

Esta es la versión web de la aplicación Audio DAW con integración MVSep.

## 🚀 Acceso

La web está disponible en:
```
https://clubkaraoke.github.io/VOCAL_REMOVER_CLOUDE/
```

## 📱 Características (Demo)

- ✅ Interfaz bonita y responsiva
- ✅ Ejemplo de proyecto con 6 pistas
- ✅ Controles de reproducción
- ✅ Sliders de volumen
- ✅ Botón de sincronización
- ✅ Botón de exportación

## 🔌 Para funcionalidad REAL

Esta es una demo. Para que funcione 100% con MVSep:

1. **Instala el servidor local:**
   ```bash
   git clone https://github.com/clubkaraoke/VOCAL_REMOVER_CLOUDE
   cd VOCAL_REMOVER_CLOUDE
   pip install -r requirements.txt
   ```

2. **Configura tu token MVSep:**
   ```bash
   cp .env.example .env
   # Edita .env y agrega tu MVSEP_API_TOKEN
   ```

3. **Corre el servidor:**
   ```bash
   python -m uvicorn app.main:app --reload
   ```

4. **Abre:**
   ```
   http://localhost:8000
   ```

## 🛠️ Archivos

- `index.html` - Web standalone (completamente funcional sin servidor)
- `../app/` - Backend FastAPI (servidor local)
- `../requirements.txt` - Dependencias Python

## 📞 Soporte

- Repo: https://github.com/clubkaraoke/VOCAL_REMOVER_CLOUDE
- Issues: Abre un issue en GitHub

## 🎉 ¡Disfruta!

🎵 Audio DAW - Hecho por Augusto
