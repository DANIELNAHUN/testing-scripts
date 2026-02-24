from gtts import gTTS
import pyttsx3
import os

path_results = "files/results/output.mp3"

def texto_a_voz_with_gtts(texto, idioma='es', nombre_archivo=path_results):
    try:
        # Crear el objeto de texto a voz
        tts = gTTS(text=texto, lang=idioma, slow=False)
        
        # Guardar el archivo de audio
        tts.save(nombre_archivo)
        print(f"Archivo de audio guardado como: {nombre_archivo}")
        
        # # Reproducir el archivo de audio (opcional)
        # os.system(f"start {nombre_archivo}" if os.name == "nt" else f"xdg-open {nombre_archivo}")
    except Exception as e:
        print(f"Error al convertir texto a voz: {e}")


def texto_a_voz_with_pyttsx3(texto, nombre_archivo=path_results):
    try:
        # Inicializar el motor de texto a voz
        engine = pyttsx3.init()
        
        # Configuración opcional: velocidad de habla
        engine.setProperty('rate', 150)  # Valor por defecto ~200
        
        # Configuración opcional: volumen de voz
        engine.setProperty('volume', 0.8)  # 0.0 a 1.0
        
        # Configuración opcional: elegir voz (masculina/femenina)
        voices = engine.getProperty('voices')
        engine.setProperty('voice', voices[0].id)  # 0 para masculino, 1 para femenino en muchos sistemas

        # Ejecutar y esperar a que termine
        engine.runAndWait()

        # guardar en archivo (opcional)
        engine.save_to_file(texto, nombre_archivo)
        
        # # Convertir texto a voz
        # engine.say(texto)
        

    except Exception as e:
        print(f"Error al convertir texto a voz: {e}")

def texto_a_voz_desde_archivo(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            texto = f.read()
            texto_a_voz_with_pyttsx3(texto)
            # texto_a_voz_with_gtts(texto)
    except Exception as e:
        print(f"Error al leer el archivo: {e}")

# Ejemplo de uso
if __name__ == "__main__":
    texto = "Hola, este es un ejemplo de conversión de texto a voz usando Python."
    # texto_a_voz_with_gtts(texto)
    # texto_a_voz_with_pyttsx3(texto)
    texto_a_voz_desde_archivo("files/source/CleanCode.txt")