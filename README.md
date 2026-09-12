# 🎵 Audio DAW - MVSep Integration

Web DAW para editar y exportar proyectos de separación de audio desde MVSep.

## ✨ Features

- ✅ Sincroniza automáticamente tu histórico de proyectos desde MVSep
- ✅ Interfaz web bonita y profesional (Tailwind CSS)
- ✅ Reproduce cada pista independientemente
- ✅ Controles de volumen por pista
- ✅ Exporta mezclas personalizadas
- ✅ Sin GPU requerida
- ✅ Integración 100% con MVSep API

## 🚀 Quick Start

### 1. Requisitos

- Python 3.9+
- ffmpeg instalado (`apt-get install ffmpeg` en Linux)
- Token de MVSep (obtén en https://mvsep.com/settings)

### 2. Setup

```bash
# Clonar repo
git clone https://github.com/clubkaraoke/VOCAL_REMOVER_CLOUDE
cd VOCAL_REMOVER_CLOUDE

# Instalar dependencias
pip install -r requirements.txt

# Crear archivo .env
cp .env.example .env

# Editar .env y agregar tu token
# MVSEP_API_TOKEN=sk_live_YOUR_TOKEN_HERE
nano .env
```

### 3. Correr la app

```bash
# Opción 1: Desarrollo
python -m uvicorn app.main:app --reload

# Opción 2: Producción
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 4. Abrir en navegador

```
http://localhost:8000
```

## 📁 Estructura

```
VOCAL_REMOVER_CLOUDE/
├── app/
│   ├── main.py                  # Backend FastAPI
│   ├── database.py              # SQLite management
│   ├── mvsep_client.py          # MVSep API client
│   ├── templates/
│   │   └── index.html           # Frontend web
│   └── daw.db                   # Database (auto-created)
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
├── .gitignore
└── README.md
```

## 🎯 Uso

1. **Sincronizar MVSep**: Click en "🔄 Sincronizar MVSep"
   - Trae todos tus proyectos completados desde MVSep
   - Los guarda en la base de datos local

2. **Seleccionar Proyecto**: Click en un proyecto en la sidebar
   - Carga todas las pistas del proyecto

3. **Reproducir**: Usa los controles de audio o botón Play
   - Cada pista tiene controles independientes

4. **Exportar**: Click en "⬇️ Descargar Mezcla"
   - Mezcla todas las pistas
   - Descarga como MP3, WAV o FLAC

## 🔐 Configuración

### Variables en `.env`

```
# Requerido
MVSEP_API_TOKEN=sk_live_YOUR_TOKEN_HERE

# Optional
DEBUG=True
MAX_FILE_SIZE=500
MAX_PROJECTS=100
API_HOST=0.0.0.0
API_PORT=8000
```

## 🛠️ API Endpoints

```
GET  /                              → Frontend
GET  /health                        → Health check

POST /api/sync-mvsep                → Sincronizar MVSep
GET  /api/projects                  → Listar proyectos
GET  /api/projects/{id}             → Obtener proyecto
POST /api/projects/{id}/export      → Exportar mezcla
POST /api/projects/{id}/silent-regions → Guardar silencios
```

## 🐛 Troubleshooting

### Error: "MVSEP_API_TOKEN no está seteado"
```
→ Edita .env con tu token
→ Asegúrate de usar format: sk_live_...
```

### Error: "ffmpeg not found"
```bash
# Linux
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Descarga desde https://ffmpeg.org/download.html
```

### Base de datos corrupta
```bash
# Borrar y recrear
rm app/daw.db

# Correr la app de nuevo (se crea automáticamente)
python -m uvicorn app.main:app --reload
```

## 📚 Documentación completa

Ver archivos en `/docs`:
- `SPLEETER-WEB-ANALYSIS-REPO.md` — Análisis arquitectónico
- `EXECUTION-PLAN-MVSEP-ADAPTATION.md` — Plan de implementación
- `CODE-SNIPPETS-CHANGES.md` — Cambios técnicos

## 🤝 Contribuir

Pull requests bienvenidas. Para cambios mayores, abre un issue primero.

## 📄 License

MIT License

## 👤 Autor

**Augusto** - @clubkaraoke

---

**¿Preguntas?** Abre un issue en GitHub o contacta en Discord.

🎵 **¡A disfrutar tu DAW!** 🎵
