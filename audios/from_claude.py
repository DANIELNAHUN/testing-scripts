from pydub import AudioSegment
from pydub.effects import normalize
from pedalboard import Pedalboard, Reverb
import numpy as np
import os

# ── 1. EFECTO ECO/REVERB AL LOCUTOR ──────────────────────────
board = Pedalboard([
    Reverb(
        room_size=0.3,       # pequeño = proyección de voz, no cueva
        damping=0.7,         # amortigua los reflejos altos
        wet_level=0.2,       # 20% reverb mezclado con la voz seca
        dry_level=0.8        # 80% voz original
    )
])

path_of_audios_source = 'files/source'
path_of_audios_target = 'files/results'

# Audios Locutor
audio_1 = os.path.join(path_of_audios_source, "Gran Campaña - Introduccion.wav")
audio_2 = os.path.join(path_of_audios_source, "Gran Campaña - Cuerpo.wav")
audio_3 = os.path.join(path_of_audios_source, "Gran Campaña - Cierre.wav")

# Audios Música
audio_4 = os.path.join(path_of_audios_source, "Eres todo Poderoso.mp3")
audio_5 = os.path.join(path_of_audios_source, "Yo tengo un amigo que me ama.mp3")

# ── 2. UNIR PARTES DEL LOCUTOR ────────────────────────────────
locutor = AudioSegment.from_mp3(audio_1) + \
          AudioSegment.from_mp3(audio_2) + \
          AudioSegment.from_mp3(audio_3)

total_ms = len(locutor)  # duración total en milisegundos

# ── 3. FONDOS MUSICALES ───────────────────────────────────────
INTRO_DURATION_MS = 10000  # fondo1 siempre = 10 segundos fijos

fondo1 = AudioSegment.from_mp3(audio_4)[:INTRO_DURATION_MS]
fondo2_raw = AudioSegment.from_mp3(audio_5)

# Alargar fondo2 en loop si es más corto que el locutor
while len(fondo2_raw) < total_ms:
    fondo2_raw += fondo2_raw
fondo2 = fondo2_raw[:total_ms]  # recortar/alargar exacto

# ── 4. DUCKING: bajar fondo cuando habla el locutor ───────────
fondo2_ducked = fondo2 - 15  # bajar 15 dB mientras habla

# ── 5. FADE IN/OUT en los fondos musicales ────────────────────
fondo1 = fondo1.fade_in(2000).fade_out(2000)     # 2 seg de fade
fondo2_ducked = fondo2_ducked.fade_in(1000).fade_out(3000)

# ── 6. MEZCLA FINAL ───────────────────────────────────────────
intro = fondo1.overlay(locutor[:INTRO_DURATION_MS])
cuerpo = fondo2_ducked.overlay(locutor[INTRO_DURATION_MS:])
final = intro + cuerpo

final.export(os.path.join(path_of_audios_target, "produccion_final.mp3"), format="mp3", bitrate="192k")