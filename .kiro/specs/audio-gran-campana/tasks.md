# Implementation Plan: Audio Gran Campaña

## Overview

Este plan implementa un sistema de procesamiento de audio automatizado en Python que combina archivos de locutor con fondos musicales aplicando efectos de volumen y transiciones. El sistema utiliza pydub para manipulación de audio y sigue un patrón de pipeline secuencial con 6 componentes principales: FileLoader, LocutorProcessor, BackgroundMusicProcessor, AudioCombiner, AudioExporter, y AudioProcessor (orquestador).

## Tasks

- [x] 1. Configurar estructura del proyecto y dependencias
  - Crear estructura de directorios (src/, tests/, files/source/, files/output/)
  - Crear requirements.txt con dependencias (pydub, pytest, hypothesis)
  - Crear archivo README.md con instrucciones de instalación de ffmpeg
  - Configurar logging básico del sistema
  - _Requirements: 1.1, 9.2_

- [x] 2. Implementar modelos de datos y excepciones
  - [x] 2.1 Crear data models (LocutorResult, BackgroundResult, ProcessingResult)
    - Implementar dataclasses con todos los campos especificados en el diseño
    - _Requirements: 2.3, 2.5, 3.5, 6.6, 9.5_
  
  - [x] 2.2 Crear jerarquía de excepciones
    - Implementar AudioProcessingError, MissingFileError, ValidationError
    - _Requirements: 10.1, 10.2_

- [x] 3. Implementar FileLoader
  - [x] 3.1 Crear clase FileLoader con métodos load_audio y load_multiple
    - Implementar carga de archivos WAV y MP3 usando pydub.AudioSegment
    - Retornar None cuando archivo no existe (no lanzar excepción)
    - Agregar logging de archivos cargados y omitidos
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 10.4, 10.5_
  
  - [x] 3.2 Escribir property test para Property 1 (Multi-format Audio Loading)
    - **Property 1: Multi-format Audio Loading**
    - **Validates: Requirements 1.4, 1.5**
    - Generar archivos de audio sintéticos en WAV y MP3
    - Verificar que FileLoader carga ambos formatos correctamente
  
  - [x] 3.3 Escribir property test para Property 2 (Graceful Handling of Missing Files)
    - **Property 2: Graceful Handling of Missing Files**
    - **Validates: Requirements 1.3, 2.2, 10.3**
    - Generar patrones aleatorios de archivos existentes/faltantes
    - Verificar que el sistema continúa sin lanzar excepciones
  
  - [x] 3.4 Escribir unit tests para FileLoader
    - Test carga de archivo WAV específico
    - Test carga de archivo MP3 específico
    - Test manejo de archivo inexistente
    - Test carga múltiple con mix de formatos
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [ ] 4. Implementar LocutorProcessor
  - [x] 4.1 Crear clase LocutorProcessor con método unify_locutor_audio
    - Definir constante LOCUTOR_SEQUENCE con los 5 archivos en orden
    - Implementar concatenación de archivos en orden específico
    - Omitir archivos faltantes y continuar con los siguientes
    - Calcular y almacenar duración total del locutor unificado
    - Retornar LocutorResult con metadata completa
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_
  
  - [x] 4.2 Escribir property test para Property 3 (Concatenation Order Preservation)
    - **Property 3: Concatenation Order Preservation**
    - **Validates: Requirements 2.1**
    - Generar secuencias aleatorias de archivos de audio
    - Verificar que el orden de concatenación se preserva exactamente
  
  - [x] 4.3 Escribir property test para Property 4 (Duration Summation in Concatenation)
    - **Property 4: Duration Summation in Concatenation**
    - **Validates: Requirements 2.5**
    - Generar segmentos de audio con duraciones aleatorias
    - Verificar que duración total = suma de duraciones individuales
  
  - [x] 4.4 Escribir property test para Property 5 (Audio Quality Preservation in Concatenation)
    - **Property 5: Audio Quality Preservation in Concatenation**
    - **Validates: Requirements 2.4**
    - Generar segmentos con diferentes sample rates y bit depths
    - Verificar que las propiedades de audio se preservan
  
  - [x] 4.5 Escribir unit tests para LocutorProcessor
    - Test con todos los archivos presentes
    - Test con primer archivo faltante
    - Test con todos los archivos faltantes (debe lanzar MissingFileError)
    - Test verificación de orden específico de archivos
    - _Requirements: 2.1, 2.2, 10.2_

- [x] 5. Checkpoint - Verificar carga y concatenación de locutor
  - Ejecutar tests de FileLoader y LocutorProcessor
  - Verificar que todos los tests pasan
  - Preguntar al usuario si hay dudas o ajustes necesarios

- [ ] 6. Implementar BackgroundMusicProcessor - Parte 1 (Primer fondo)
  - [x] 6.1 Crear clase BackgroundMusicProcessor con método process_first_background
    - Definir constantes FIRST_BACKGROUND, SECOND_BACKGROUND, CROSSFADE_DURATION
    - Cargar archivo 'Yo tengo un amigo que me ama.mp3'
    - Aplicar 100% volumen a primeros 4 segundos
    - Aplicar fade de 100% a 25% entre segundo 4 y 5 (usando pydub fade)
    - Aplicar 25% volumen al resto del audio
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_
  
  - [x] 6.2 Escribir property test para Property 6 (First Background Volume Profile)
    - **Property 6: First Background Volume Profile**
    - **Validates: Requirements 3.2, 3.3, 3.4**
    - Generar archivos de audio con duraciones aleatorias
    - Verificar perfil de volumen: 100% primeros 4s, fade 4-5s, 25% resto
  
  - [x] 6.3 Escribir property test para Property 7 (First Background Duration Preservation)
    - **Property 7: First Background Duration Preservation**
    - **Validates: Requirements 3.1, 3.5**
    - Generar archivos con duraciones aleatorias
    - Verificar que duración de salida = duración de entrada

- [ ] 7. Implementar BackgroundMusicProcessor - Parte 2 (Segundo fondo)
  - [x] 7.1 Implementar método calculate_second_background_duration
    - Implementar fórmula: locutor_duration + 10s - first_bg_duration + 3s
    - Agregar logging de la duración calculada
    - _Requirements: 4.1, 4.2_
  
  - [x] 7.2 Implementar método process_second_background
    - Cargar archivo 'Eres todo poderoso.mp3'
    - Verificar si archivo tiene duración suficiente
    - Recortar a duración calculada (o usar duración completa si es menor)
    - Aplicar 20% volumen excepto últimos 5 segundos
    - Aplicar fade de 20% a 100% comenzando 4 segundos antes del final
    - Aplicar 100% volumen al último segundo
    - _Requirements: 4.3, 4.4, 5.1, 5.2, 5.3, 5.4_
  
  - [x] 7.3 Escribir property test para Property 8 (Second Background Duration Calculation)
    - **Property 8: Second Background Duration Calculation**
    - **Validates: Requirements 4.1**
    - Generar duraciones aleatorias de locutor y primer fondo
    - Verificar fórmula: L + 10000ms - F + 3000ms
  
  - [x] 7.4 Escribir property test para Property 9 (Second Background Duration Fallback)
    - **Property 9: Second Background Duration Fallback**
    - **Validates: Requirements 4.4**
    - Generar casos donde segundo fondo es más corto que lo requerido
    - Verificar que usa duración completa sin error
  
  - [x] 7.5 Escribir property test para Property 10 (Second Background Volume Profile)
    - **Property 10: Second Background Volume Profile**
    - **Validates: Requirements 5.2, 5.3, 5.4**
    - Generar archivos con duraciones aleatorias
    - Verificar perfil: 20% excepto últimos 5s, fade últimos 4s, 100% último segundo
  
  - [x] 7.6 Escribir property test para Property 11 (Second Background Trimming)
    - **Property 11: Second Background Trimming**
    - **Validates: Requirements 5.1**
    - Generar duraciones calculadas aleatorias
    - Verificar que salida tiene exactamente la duración calculada (o completa si menor)

- [x] 8. Implementar BackgroundMusicProcessor - Parte 3 (Unificación)
  - [x] 8.1 Implementar método unify_backgrounds
    - Aplicar crossfade de 3 segundos entre ambos fondos usando pydub.append
    - Calcular duración total del fondo unificado
    - Retornar BackgroundResult con metadata completa
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_
  
  - [x] 8.2 Escribir property test para Property 12 (Crossfade Duration and Position)
    - **Property 12: Crossfade Duration and Position**
    - **Validates: Requirements 6.2, 6.6**
    - Generar pares de segmentos con duraciones aleatorias
    - Verificar duración total = first + second - 3000ms
    - Verificar overlap de 3 segundos
  
  - [x] 8.3 Escribir property test para Property 13 (Background Unification Completeness)
    - **Property 13: Background Unification Completeness**
    - **Validates: Requirements 6.1, 6.5**
    - Generar pares de segmentos aleatorios
    - Verificar que salida contiene contenido de ambos segmentos
  
  - [x] 8.4 Escribir unit tests para BackgroundMusicProcessor
    - Test procesamiento de primer fondo con archivo específico
    - Test cálculo de duración de segundo fondo
    - Test procesamiento de segundo fondo
    - Test unificación con crossfade
    - Test error cuando archivos de fondo faltan (MissingFileError)
    - _Requirements: 3.1, 4.1, 5.1, 6.1, 10.1_

- [ ] 9. Checkpoint - Verificar procesamiento de fondos musicales
  - Ejecutar tests de BackgroundMusicProcessor
  - Verificar que todos los tests pasan
  - Preguntar al usuario si hay dudas o ajustes necesarios

- [ ] 10. Implementar AudioCombiner
  - [x] 10.1 Crear clase AudioCombiner con método combine
    - Definir constante LOCUTOR_START_OFFSET = 5000ms
    - Implementar overlay del locutor sobre el fondo musical usando pydub.overlay
    - Iniciar locutor a los 5 segundos del fondo
    - Mantener locutor a 100% volumen
    - Aplicar fade al fondo musical de volumen actual a 100% cuando termina locutor
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_
  
  - [x] 10.2 Implementar método validate_durations
    - Verificar que background_duration = locutor_duration + 10000ms (con tolerancia)
    - Verificar que locutor termina al menos 5000ms antes del final
    - Retornar bool indicando si validación pasó
    - Agregar logging de warnings si validación falla
    - _Requirements: 8.1, 8.2, 8.3, 8.4_
  
  - [x] 10.3 Escribir property test para Property 14 (Locutor Overlay Timing)
    - **Property 14: Locutor Overlay Timing**
    - **Validates: Requirements 7.2, 8.2**
    - Generar pares de locutor y fondo con duraciones aleatorias
    - Verificar que locutor inicia exactamente a 5000ms
  
  - [x] 10.4 Escribir property test para Property 15 (Locutor Volume Preservation)
    - **Property 15: Locutor Volume Preservation**
    - **Validates: Requirements 7.3**
    - Generar locutores con duraciones aleatorias
    - Verificar que volumen del locutor se mantiene a 100% en toda su duración
  
  - [x] 10.5 Escribir property test para Property 16 (Background Fade After Locutor)
    - **Property 16: Background Fade After Locutor**
    - **Validates: Requirements 7.4**
    - Generar combinaciones donde locutor termina antes que fondo
    - Verificar que fondo hace fade a 100% después de que termina locutor
  
  - [x] 10.6 Escribir property test para Property 17 (Duration Synchronization Validation)
    - **Property 17: Duration Synchronization Validation**
    - **Validates: Requirements 8.1, 8.3**
    - Generar duraciones aleatorias de locutor y fondo
    - Verificar que B = L + 10000ms (con tolerancia)
    - Verificar que locutor termina al menos 5000ms antes del final
  
  - [x] 10.7 Escribir unit tests para AudioCombiner
    - Test overlay con timing correcto (5 segundos)
    - Test validación de duraciones con valores correctos
    - Test validación de duraciones con valores incorrectos (debe logear warning)
    - Test fade de fondo después de que termina locutor
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 8.1, 8.2, 8.3_

- [x] 11. Implementar AudioExporter
  - [x] 11.1 Crear clase AudioExporter con método export
    - Definir constante MIN_BITRATE = "192k"
    - Implementar exportación a MP3 usando audio.export()
    - Configurar bitrate mínimo de 192 kbps
    - Preservar propiedades de audio (sample rate, channels)
    - Agregar logging del path de salida y duración
    - Retornar Path del archivo exportado
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_
  
  - [x] 11.2 Escribir property test para Property 18 (MP3 Export Format and Quality)
    - **Property 18: MP3 Export Format and Quality**
    - **Validates: Requirements 9.1, 9.3**
    - Generar archivos de audio aleatorios
    - Exportar a MP3 y verificar formato y bitrate >= 192 kbps
  
  - [x] 11.3 Escribir property test para Property 19 (Export Quality Preservation)
    - **Property 19: Export Quality Preservation**
    - **Validates: Requirements 9.4**
    - Generar archivos con diferentes sample rates y channels
    - Verificar que propiedades se preservan después de exportar
  
  - [x] 11.4 Escribir unit tests para AudioExporter
    - Test exportación a MP3 con bitrate correcto
    - Test verificación de formato de salida
    - Test logging de información de exportación
    - _Requirements: 9.1, 9.2, 9.3, 9.5_

- [x] 12. Implementar AudioProcessor (orquestador principal)
  - [x] 12.1 Crear clase AudioProcessor con método process
    - Inicializar todos los componentes (FileLoader, LocutorProcessor, etc.)
    - Implementar pipeline completo en orden:
      1. Procesar locutor (LocutorProcessor.unify_locutor_audio)
      2. Procesar primer fondo (BackgroundMusicProcessor.process_first_background)
      3. Calcular duración segundo fondo
      4. Procesar segundo fondo
      5. Unificar fondos
      6. Combinar locutor con fondo
      7. Validar duraciones
      8. Exportar audio final
    - Manejar excepciones y retornar ProcessingResult con success=False en caso de error
    - Agregar logging de cada etapa del pipeline
    - _Requirements: 1.1, 2.1, 3.1, 4.1, 5.1, 6.1, 7.1, 8.1, 9.1_
  
  - [x] 12.2 Escribir property test para Property 20 (Required File Validation)
    - **Property 20: Required File Validation**
    - **Validates: Requirements 10.1**
    - Generar escenarios donde archivos de fondo requeridos faltan
    - Verificar que se lanza MissingFileError antes de procesar
  
  - [x] 12.3 Escribir property test para Property 21 (Empty Locutor Validation)
    - **Property 21: Empty Locutor Validation**
    - **Validates: Requirements 10.2**
    - Generar escenarios donde todos los archivos de locutor faltan
    - Verificar que se lanza MissingFileError
  
  - [x] 12.4 Escribir property test para Property 22 (File Loading Status Logging)
    - **Property 22: File Loading Status Logging**
    - **Validates: Requirements 10.4, 10.5**
    - Generar patrones aleatorios de archivos presentes/faltantes
    - Verificar que logs contienen lista completa de archivos cargados y omitidos
  
  - [x] 12.5 Escribir unit tests para AudioProcessor
    - Test pipeline completo con todos los archivos presentes (happy path)
    - Test con algunos archivos de locutor faltantes
    - Test error cuando faltan archivos de fondo
    - Test error cuando faltan todos los archivos de locutor
    - Test que ProcessingResult contiene toda la metadata correcta
    - _Requirements: 1.1, 2.1, 3.1, 4.1, 5.1, 6.1, 7.1, 8.1, 9.1, 10.1, 10.2_

- [ ] 13. Checkpoint - Verificar integración completa
  - Ejecutar todos los tests (unit y property-based)
  - Verificar que todos los tests pasan
  - Verificar cobertura de código (objetivo: 90% líneas, 85% branches)
  - Preguntar al usuario si hay dudas o ajustes necesarios

- [x] 14. Crear script principal y archivos de audio de prueba
  - [x] 14.1 Crear script main.py para ejecutar el procesamiento
    - Implementar CLI simple que ejecute AudioProcessor
    - Agregar manejo de argumentos para carpetas de entrada/salida
    - Agregar manejo de excepciones y mensajes de error claros
    - _Requirements: 9.2, 9.5_
  
  - [x] 14.2 Generar archivos de audio sintéticos para testing
    - Crear archivos de prueba en tests/fixtures/audio/
    - Generar archivos de locutor en WAV y MP3
    - Generar archivos de fondo musical en MP3
    - Crear archivos con diferentes duraciones para edge cases
  
  - [x] 14.3 Escribir integration tests end-to-end
    - Test pipeline completo con archivos de prueba reales
    - Test con diferentes combinaciones de archivos presentes/faltantes
    - Test verificación de archivo de salida generado
    - Verificar que archivo de salida tiene formato y calidad correctos
    - _Requirements: 1.1, 2.1, 3.1, 4.1, 5.1, 6.1, 7.1, 8.1, 9.1_

- [x] 15. Configurar property-based tests con Hypothesis
  - [x] 15.1 Crear estrategias personalizadas de Hypothesis
    - Crear strategy para generar AudioSegments con duraciones aleatorias
    - Crear strategy para generar patrones de archivos existentes/faltantes
    - Crear strategy para generar propiedades de audio aleatorias (sample rate, channels)
  
  - [x] 15.2 Configurar settings de Hypothesis
    - Configurar mínimo 100 iteraciones por test
    - Configurar timeout apropiado para tests de audio
    - Agregar decoradores @given a todos los property tests

- [ ] 16. Checkpoint final - Validación completa
  - Ejecutar suite completa de tests (unit, property-based, integration)
  - Verificar que todos los tests pasan
  - Verificar que todas las 22 propiedades tienen property tests implementados
  - Generar reporte de cobertura de código
  - Ejecutar el script main.py con archivos de prueba para validación manual
  - Preguntar al usuario si el sistema cumple con todas las expectativas

## Notes

- Las tareas marcadas con `*` son opcionales y pueden omitirse para un MVP más rápido
- Cada tarea referencia los requisitos específicos para trazabilidad
- Los checkpoints aseguran validación incremental del progreso
- Los property tests validan las 22 propiedades de correctitud universales
- Los unit tests validan ejemplos específicos y casos edge
- Se requiere ffmpeg instalado en el sistema para que pydub funcione correctamente
- Hypothesis debe configurarse con mínimo 100 iteraciones por property test
