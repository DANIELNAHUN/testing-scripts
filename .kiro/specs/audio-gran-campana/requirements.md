# Requirements Document

## Introduction

El sistema Audio Gran Campaña es un procesador de audio automatizado que combina múltiples archivos de audio de locutor con fondos musicales, aplicando efectos de volumen y transiciones para crear una producción de audio final profesional. El sistema lee archivos de audio desde una carpeta de origen, los procesa según especificaciones de orden, duración y volumen, y genera un archivo de audio final unificado.

## Glossary

- **Audio_Processor**: El sistema que procesa y combina archivos de audio
- **Locutor_Audio**: Archivos de audio que contienen la narración hablada
- **Fondo_Musical**: Archivos de audio que contienen música de fondo
- **Source_Folder**: Carpeta files/source que contiene los archivos de audio originales
- **Locutor_Unificado**: Archivo de audio resultante de unir todos los audios de locutor en el orden especificado
- **Fondo_Musical_Unificado**: Archivo de audio resultante de procesar y unir los fondos musicales
- **Audio_Final**: Archivo de audio resultante de combinar el Locutor_Unificado con el Fondo_Musical_Unificado
- **Volume_Fade**: Efecto de transición gradual de volumen (subida o bajada)
- **Crossfade**: Efecto de transición suave entre dos audios donde uno baja de volumen mientras el otro sube

## Requirements

### Requirement 1: Leer Archivos de Audio de Locutor

**User Story:** Como usuario del sistema, quiero que el sistema lea los archivos de audio de locutor desde la carpeta de origen, para poder procesarlos posteriormente.

#### Acceptance Criteria

1. THE Audio_Processor SHALL read audio files from the Source_Folder
2. WHEN a Locutor_Audio file exists in the Source_Folder, THE Audio_Processor SHALL load it into memory
3. WHEN a Locutor_Audio file does not exist in the Source_Folder, THE Audio_Processor SHALL skip it and continue processing
4. THE Audio_Processor SHALL support WAV format for Locutor_Audio files
5. THE Audio_Processor SHALL support MP3 format for Locutor_Audio files

### Requirement 2: Unificar Audios de Locutor en Orden Específico

**User Story:** Como usuario del sistema, quiero que los audios de locutor se unan en un orden específico, para crear una narración coherente.

#### Acceptance Criteria

1. THE Audio_Processor SHALL concatenate Locutor_Audio files in the following order: 'Gran Campaña - Introduccion.wav', 'Gran Campaña - Hora y lugar del evento.mp3', 'Gran Campaña - Cuerpo.wav', 'Gran Campaña - Hora y lugar del evento.mp3', 'Gran Campaña - Cierre.wav'
2. WHEN a Locutor_Audio file in the sequence does not exist, THE Audio_Processor SHALL skip that position and continue with the next file
3. THE Audio_Processor SHALL generate a Locutor_Unificado file containing all concatenated Locutor_Audio files
4. THE Audio_Processor SHALL preserve the original audio quality during concatenation
5. THE Audio_Processor SHALL calculate and store the total duration of the Locutor_Unificado file

### Requirement 3: Procesar Primer Fondo Musical con Efectos de Volumen

**User Story:** Como usuario del sistema, quiero que el primer fondo musical tenga efectos de volumen específicos, para crear una introducción profesional.

#### Acceptance Criteria

1. THE Audio_Processor SHALL use the complete duration of the first Fondo_Musical file 'Yo tengo un amigo que me ama.mp3'
2. THE Audio_Processor SHALL apply 100% volume to the first 5 seconds of the first Fondo_Musical
3. THE Audio_Processor SHALL apply a Volume_Fade effect starting at second 4 that reduces volume from 100% to 25% by second 5
4. THE Audio_Processor SHALL maintain 25% volume for the remaining duration of the first Fondo_Musical
5. THE Audio_Processor SHALL calculate and store the total duration of the processed first Fondo_Musical

### Requirement 4: Calcular Duración del Segundo Fondo Musical

**User Story:** Como usuario del sistema, quiero que el sistema calcule automáticamente la duración necesaria del segundo fondo musical, para que el audio final tenga la duración correcta.

#### Acceptance Criteria

1. THE Audio_Processor SHALL calculate the required duration of the second Fondo_Musical using the formula: Duration_Locutor_Unificado + 10 seconds - Duration_First_Fondo_Musical + 3 seconds
2. THE Audio_Processor SHALL add 3 seconds to the calculated duration to compensate for the 3 seconds that will be used in the Crossfade transition
3. THE Audio_Processor SHALL verify that the second Fondo_Musical file 'Eres todo poderoso.mp3' has sufficient duration
4. WHEN the second Fondo_Musical is shorter than the calculated duration, THE Audio_Processor SHALL use the complete available duration
5. THE Audio_Processor SHALL store the calculated duration for subsequent processing

### Requirement 5: Procesar Segundo Fondo Musical con Efectos de Volumen

**User Story:** Como usuario del sistema, quiero que el segundo fondo musical tenga efectos de volumen específicos, para crear un cierre profesional.

#### Acceptance Criteria

1. THE Audio_Processor SHALL trim the second Fondo_Musical to the calculated duration from Requirement 4
2. THE Audio_Processor SHALL apply 20% volume to the entire second Fondo_Musical except the last 5 seconds
3. THE Audio_Processor SHALL apply a Volume_Fade effect starting at 4 seconds before the end that increases volume from 20% to 100%
4. THE Audio_Processor SHALL apply 100% volume to the last second of the second Fondo_Musical

### Requirement 6: Unificar Fondos Musicales con Transición Suave

**User Story:** Como usuario del sistema, quiero que los dos fondos musicales se unan con una transición suave, para evitar cambios bruscos en la música.

#### Acceptance Criteria

1. THE Audio_Processor SHALL concatenate the processed first Fondo_Musical with the processed second Fondo_Musical
2. THE Audio_Processor SHALL apply a Crossfade effect with a duration of 3 seconds at the transition point between both Fondo_Musical files
3. THE Audio_Processor SHALL use the first 3 seconds of the second Fondo_Musical for the Crossfade transition
4. DURING the Crossfade, THE Audio_Processor SHALL overlap the last 3 seconds of the first Fondo_Musical with the first 3 seconds of the second Fondo_Musical
5. THE Audio_Processor SHALL generate a Fondo_Musical_Unificado file containing both processed Fondo_Musical files with smooth transition
6. THE Audio_Processor SHALL calculate and store the total duration of the Fondo_Musical_Unificado

### Requirement 7: Combinar Locutor con Fondo Musical

**User Story:** Como usuario del sistema, quiero que el audio del locutor se combine con el fondo musical de manera sincronizada, para crear una producción de audio profesional.

#### Acceptance Criteria

1. THE Audio_Processor SHALL overlay the Locutor_Unificado on top of the Fondo_Musical_Unificado
2. THE Audio_Processor SHALL start the Locutor_Unificado at 5 seconds from the beginning of the Fondo_Musical_Unificado
3. THE Audio_Processor SHALL maintain the Locutor_Unificado at 100% volume throughout its duration
4. WHEN the Locutor_Unificado ends, THE Audio_Processor SHALL apply a Volume_Fade effect to increase the Fondo_Musical_Unificado from its current volume to 100%
5. THE Audio_Processor SHALL generate an Audio_Final file containing the combined audio

### Requirement 8: Validar Sincronización de Duración Total

**User Story:** Como usuario del sistema, quiero que el sistema valide que todas las duraciones calculadas sean correctas, para asegurar que el audio final tenga la sincronización perfecta.

#### Acceptance Criteria

1. THE Audio_Processor SHALL verify that the Fondo_Musical_Unificado duration equals Duration_Locutor_Unificado + 10 seconds
2. THE Audio_Processor SHALL verify that the Locutor_Unificado starts at second 5 of the Audio_Final
3. THE Audio_Processor SHALL verify that the Locutor_Unificado ends at least 5 seconds before the Audio_Final ends
4. WHEN duration validation fails, THE Audio_Processor SHALL log a warning message with the discrepancy details

### Requirement 9: Generar Archivo de Audio Final

**User Story:** Como usuario del sistema, quiero que el sistema genere un archivo de audio final en formato MP3, para poder utilizarlo en producciones.

#### Acceptance Criteria

1. THE Audio_Processor SHALL export the Audio_Final in MP3 format
2. THE Audio_Processor SHALL save the Audio_Final to the output directory
3. THE Audio_Processor SHALL use a bitrate of at least 192 kbps for the Audio_Final
4. THE Audio_Processor SHALL preserve audio quality during the export process
5. WHEN the export is successful, THE Audio_Processor SHALL log the output file path and duration

### Requirement 10: Manejo de Errores de Archivos Faltantes

**User Story:** Como usuario del sistema, quiero que el sistema maneje apropiadamente los archivos faltantes, para poder identificar problemas en la configuración.

#### Acceptance Criteria

1. WHEN a required Fondo_Musical file does not exist, THE Audio_Processor SHALL log an error message and terminate processing
2. WHEN all Locutor_Audio files are missing, THE Audio_Processor SHALL log an error message and terminate processing
3. WHEN at least one Locutor_Audio file exists, THE Audio_Processor SHALL continue processing with available files
4. THE Audio_Processor SHALL log the list of successfully loaded files at the start of processing
5. THE Audio_Processor SHALL log the list of skipped files due to non-existence
