import os
from pydub import AudioSegment
from pydub.effects import normalize
import librosa
import numpy as np
import soundfile as sf

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

def cargar_audio(ruta):
    return AudioSegment.from_file(ruta)

def guardar_audio(audio, nombre):
    ruta_salida = os.path.join(CARPETA_SALIDA, nombre)
    audio.export(ruta_salida, format="mp3")
    print(f"Guardado: {ruta_salida}")

# 1. EFECTO DE PROYECCIÓN (Eco sutil / Reverb simulado)
# Para que no suene a "doble voz", el retraso debe ser muy corto (< 50ms) y bajo volumen
def aplicar_proyeccion(voice_segment, delay_ms=40, decay_db=-15):
    # Creamos una copia desplazada en el tiempo
    echo = voice_segment(delay_ms).fade_out(100) # Pequeño fade out para suavizar el corte del eco
    
    # Bajamos el volumen del eco para que sea sutil
    echo = echo - abs(decay_db)
    
    # Superponemos el eco sobre la voz original
    # El eco empieza en el tiempo 0 pero el audio está recortado, 
    # así que overlay lo pone al inicio. Para simular delay, 
    # Pydub no tiene un "shift" directo fácil, usamos un truco de silencio + overlay
    
    silence = AudioSegment.silent(duration=delay_ms)
    echo_shifted = silence + echo
    
    # Aseguramos que tengan la misma duración para overlay
    if len(echo_shifted) < len(voice_segment):
        echo_shifted = echo_shifted + AudioSegment.silent(duration=len(voice_segment) - len(echo_shifted))
    
    # Mezclamos original + eco
    projected_voice = voice_segment.overlay(echo_shifted, position=0)
    return projected_voice

# 2. UNIR PARTES DE VOZ
def unir_voces(lista_archivos_voz):
    audio_completo = AudioSegment.empty()
    for archivo in lista_archivos_voz:
        parte = cargar_audio(archivo)
        # Aplicamos efecto a cada parte antes de unir (opcional, o se puede hacer al final)
        parte_efecto = aplicar_proyeccion(voice_segment=parte)
        audio_completo += parte_efecto
    return audio_completo

# 3. PREPARAR MÚSICA DE FONDO (Fija + Variable)
def preparar_musica(archivo_fijo, archivo_variable, duracion_objetivo_segundos, duracion_fija_segundos):
    # Cargar música
    fondo1 = cargar_audio(archivo_fijo)
    fondo2 = cargar_audio(archivo_variable)
    
    # Cortar el fondo 1 a la duración fija
    fondo1 = fondo1[:duracion_fija_segundos * 1000]
    
    # Calcular cuánto falta para cubrir la voz
    duracion_restante_ms = (duracion_objetivo_segundos * 1000) - len(fondo1)
    
    if duracion_restante_ms <= 0:
        musica_final = fondo1[:duracion_objetivo_segundos * 1000]
    else:
        # Aquí usamos Librosa para estirar/encoger SIN cambiar el tono (Pitch)
        # Pydub cambia la velocidad y el tono juntos, Librosa es mejor para música
        
        # Cargar con librosa para procesamiento
        y, sr = librosa.load(archivo_variable, sr=None)
        duracion_original_seg = len(y) / sr
        duracion_restante_seg = duracion_restante_ms / 1000
        
        # Calcular factor de estiramiento
        rate = duracion_original_seg / duracion_restante_seg
        
        # Time stretch (preservando pitch)
        y_stretched = librosa.effects.time_stretch(y, rate=rate)
        
        # Guardar temporalmente el audio estirado para cargarlo con Pydub
        temp_path = os.path.join(CARPETA_SALIDA, "temp_fondo2.wav")
        sf.write(temp_path, y_stretched, sr)
        
        fondo2_ajustado = AudioSegment.from_file(temp_path)
        
        # Si por algún cálculo matemático quedó corto o largo, recortamos/exactamos
        if len(fondo2_ajustado) > duracion_restante_ms:
            fondo2_ajustado = fondo2_ajustado[:duracion_restante_ms]
        else:
            # Si quedó corto (raro con time stretch), agregamos silencio o loop
            fondo2_ajustado = fondo2_ajustado + AudioSegment.silent(duration=duracion_restante_ms - len(fondo2_ajustado))
            
        musica_final = fondo1 + fondo2_ajustado
        
    return musica_final

# 4. DUCKING AUTOMÁTICO (Bajar música cuando hay voz)
# Esta función analiza la energía de la voz y baja la música en esos segmentos
def aplicar_ducking(voz, musica, threshold_db=-40, ducking_db=-10, chunk_size_ms=100):
    # Asegurar misma duración
    if len(musica) > len(voz):
        musica = musica[:len(voz)]
    elif len(voz) > len(musica):
        voz = voz[:len(musica)]
        
    chunks = int(len(voz) / chunk_size_ms)
    musica_duckeada = AudioSegment.empty()
    
    for i in range(chunks):
        start = i * chunk_size_ms
        end = start + chunk_size_ms
        
        chunk_voz = voz[start:end]
        chunk_musica = musica[start:end]
        
        # Calcular volumen (RMS) del chunk de voz
        rms = chunk_voz.rms
        # Convertir a dB aproximado para comparar
        # Nota: 0 dBFS es el máximo, valores negativos son más bajos
        db_voz = 20 * np.log10(rms / (2**15)) if rms > 0 else -100
        
        if db_voz > threshold_db:
            # Si hay voz significativa, bajar volumen de la música
            chunk_musica = chunk_musica + ducking_db
        else:
            # Si hay silencio, subir volumen (opcional, o dejar normal)
            # Aquí podrías aplicar un fade in suave si venías de un ducking
            pass
            
        musica_duckeada += chunk_musica
        
    # Suavizar transiciones para evitar "clicks" (Crossfade simple entre chunks)
    # Pydub no permite crossfade interno fácil en un loop, 
    # para producción real se recomienda usar compresores, 
    # pero esto es una aproximación funcional.
    
    return musica_duckeada

# 5. FADE IN / FADE OUT (Inicio y Final)
def aplicar_fades(audio, fade_in_ms=2000, fade_out_ms=3000):
    return audio.fade_in(fade_in_ms).fade_out(fade_out_ms)

# --- EJECUCIÓN PRINCIPAL ---

# 1. Unir y procesar voces
archivos_voz = [audio_1, audio_2, audio_3]
voz_completa = unir_voces(archivos_voz)
duracion_total_seg = len(voz_completa) / 1000.0
print(f"Duración total de voz: {duracion_total_seg:.2f} segundos")

# 2. Preparar música
# Ejemplo: fondo1 dura 10 seg fijos, fondo2 cubre el resto
musica_completa = preparar_musica(
    archivo_fijo=audio_4, 
    archivo_variable=audio_5, 
    duracion_objetivo_segundos=duracion_total_seg,
    duracion_fija_segundos=10 
)

# 3. Aplicar Ducking (Bajar música cuando habla)
# threshold_db: Nivel a partir del cual consideramos que "habla"
# ducking_db: Cuántos dB bajar la música (ej: -15dB)
musica_procesada = aplicar_ducking(voz_completa, musica_completa, threshold_db=-35, ducking_db=-12)

# 4. Aplicar Fades generales a la música (Inicio y Fin del proyecto)
musica_procesada = aplicar_fades(musica_procesada, fade_in_ms=3000, fade_out_ms=5000)

# 5. Mezcla Final
# La música debe estar debajo de la voz (overlay)
audio_final = voz_completa.overlay(musica_procesada)

# Normalizar para evitar distorsión (clipping)
audio_final = normalize(audio_final, headroom=1.0)

guardar_audio(audio_final, "podcast_final.mp3")