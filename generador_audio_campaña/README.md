# Audio Gran Campaña

Sistema de procesamiento de audio automatizado que combina archivos de locutor con fondos musicales, aplicando efectos de volumen y transiciones para crear producciones de audio profesionales.

## Requisitos del Sistema

### FFmpeg

Este proyecto requiere FFmpeg instalado en el sistema, ya que pydub lo utiliza como backend para el procesamiento de audio.

#### Instalación de FFmpeg

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Linux (Fedora):**
```bash
sudo dnf install ffmpeg
```

**macOS (con Homebrew):**
```bash
brew install ffmpeg
```

**Windows:**
1. Descarga FFmpeg desde [ffmpeg.org](https://ffmpeg.org/download.html)
2. Extrae el archivo ZIP
3. Agrega la carpeta `bin` de FFmpeg a tu PATH del sistema

#### Verificar Instalación

Para verificar que FFmpeg está instalado correctamente:
```bash
ffmpeg -version
```

## Instalación del Proyecto

1. Clona el repositorio
2. Crea un entorno virtual (recomendado):
```bash
python -m venv env
source env/bin/activate  # En Windows: env\Scripts\activate
```

3. Instala las dependencias:
```bash
pip install -r requirements.txt
```

## Estructura del Proyecto

```
.
├── src/                    # Código fuente del sistema
├── tests/                  # Tests unitarios y property-based
├── files/
│   ├── source/            # Archivos de audio de entrada
│   └── output/            # Archivos de audio procesados
├── requirements.txt       # Dependencias del proyecto
└── README.md             # Este archivo
```

## Uso

Coloca tus archivos de audio en `files/source/` y ejecuta el procesador:

```bash
python main.py
```

El archivo de audio final se generará en `files/output/`.

## Archivos de Audio Requeridos

### Archivos de Locutor (en orden):
1. `Gran Campaña - Introduccion.wav`
2. `Gran Campaña - Hora y lugar del evento.mp3`
3. `Gran Campaña - Cuerpo.wav`
4. `Gran Campaña - Hora y lugar del evento.mp3`
5. `Gran Campaña - Cierre.wav`

### Fondos Musicales:
1. `Yo tengo un amigo que me ama.mp3`
2. `Eres todo poderoso.mp3`

**Nota:** Los archivos de locutor son opcionales (el sistema omitirá los faltantes), pero ambos fondos musicales son requeridos.

## Tests

Ejecutar todos los tests:
```bash
pytest
```

Ejecutar tests con cobertura:
```bash
pytest --cov=src --cov-report=html
```

## Tecnologías

- Python 3.8+
- pydub - Manipulación de audio
- FFmpeg - Backend de procesamiento
- pytest - Testing framework
- Hypothesis - Property-based testing
