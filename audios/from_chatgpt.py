from pedalboard import Pedalboard, Reverb, Delay
from pedalboard.io import AudioFile
import os


# Configuración de rutas
CARPETA_ENTRADA = 'files/source'
CARPETA_SALIDA = 'files/results'
os.makedirs(CARPETA_SALIDA, exist_ok=True)

# Audios Locutor
audio_1 = os.path.join(CARPETA_ENTRADA, "Gran Campaña - Introduccion.wav")
audio_2 = os.path.join(CARPETA_ENTRADA, "Gran Campaña - Cuerpo.wav")
audio_3 = os.path.join(CARPETA_ENTRADA, "Gran Campaña - Cierre.wav")

# Audios Música
audio_4 = os.path.join(CARPETA_ENTRADA, "Eres todo Poderoso.mp3")
audio_5 = os.path.join(CARPETA_ENTRADA, "Yo tengo un amigo que me ama.mp3")

board = Pedalboard([
    Delay(delay_seconds=0.06, feedback=0.15, mix=0.18),
    Reverb(room_size=0.2, wet_level=0.15)
])

with AudioFile(audio_1) as f:
    audio = f.read(f.frames)
    effected = board(audio, f.samplerate)

    with AudioFile(os.path.join(CARPETA_SALIDA, "parte1_fx.mp3"), 'w', f.samplerate, effected.shape[0]) as out:
        out.write(effected)

from pydub import AudioSegment

partes = [audio_1, audio_2, audio_3]

audio_final = AudioSegment.empty()

for p in partes:
    audio_final += AudioSegment.from_file(p)

audio_final.export(os.path.join(CARPETA_SALIDA, "voz_unida.mp3"), format="mp3")

fondo1 = AudioSegment.from_file(audio_4)[:10000]  # 10 segundos

voz = AudioSegment.from_file(os.path.join(CARPETA_SALIDA, "voz_unida.mp3"))
fondo2 = AudioSegment.from_file(audio_5)

# Repetir si es corto
while len(fondo2) < len(voz):
    fondo2 += fondo2

fondo2 = fondo2[:len(voz)]

fondo2_reducido = fondo2 - 12  # baja volumen

mezcla = fondo2_reducido.overlay(voz)

from pydub.silence import detect_nonsilent

voz = AudioSegment.from_file(os.path.join(CARPETA_SALIDA, "voz_unida.mp3"))
fondo = AudioSegment.from_file(audio_5)

segmentos = detect_nonsilent(voz, min_silence_len=400, silence_thresh=-40)

fondo_modificado = fondo

for inicio, fin in segmentos:
    fondo_modificado = fondo_modificado.overlay(
        fondo[inicio:fin] - 12,
        position=inicio
    )

final = fondo_modificado.overlay(voz)

mezcla = mezcla.fade_in(3000).fade_out(5000)
mezcla.export(os.path.join(CARPETA_SALIDA, "audio_final.mp3"), format="mp3")