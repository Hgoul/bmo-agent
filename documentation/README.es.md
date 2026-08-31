# Documentación del Proyecto BMO

*[Read this in English](README.md)*

Esta carpeta documenta el código de `be-more-agent` tal como está
actualmente en este repositorio, antes de que nada de esto se haya
desplegado en la Raspberry Pi 5. Se escribió para pasar de "aquí hay un
código que escribió otra persona" a "lo entendemos lo suficientemente
bien como para construir BMO encima de él".

Léelo en este orden:

1. **[01-code-walkthrough.md](01-code-walkthrough.md)** — qué hace
   realmente el código hoy: arquitectura, máquina de estados, el flujo
   desde la palabra de activación hasta la respuesta hablada, archivo por
   archivo.
2. **[02-whats-missing.md](02-whats-missing.md)** — por qué
   `python agent.py` **no** va a funcionar recién salido de la caja,
   incluso después de `setup.sh`. Bugs, incoherencias y partes sin
   terminar, ordenados por cuánto bloquean una primera ejecución.
3. **[03-installation-checklist.md](03-installation-checklist.md)** — la
   lista concreta y ordenada de cosas que instalar en la Pi 5 (paquetes
   del sistema, Ollama + modelos, whisper.cpp, Piper, palabra de
   activación) para conseguir una base funcional, incluyendo los pasos
   que le faltan a `setup.sh`.
4. **[04-modernization-ideas.md](04-modernization-ideas.md)** — mejoras
   opcionales: componentes que funcionan hoy pero tienen alternativas
   mejores/más rápidas/más actuales a mediados de 2026, más un boceto
   para añadir reconocimiento de voz (de hablante) de verdad, algo que el
   código actual no tiene en absoluto.
5. **[05-estado-actual-ubuntu.md](05-estado-actual-ubuntu.md)** — resumen
   de esta fase de desarrollo en un portátil Ubuntu: qué cambios de
   código se aplicaron sobre el original, todo lo instalado (y por qué
   esas versiones), y un problema de ganancia de micrófono que apareció
   y se resolvió por el camino.
6. **[06-explicacion-sencilla.md](06-explicacion-sencilla.md)** — el
   proyecto explicado sin palabras técnicas, para poder contárselo a
   alguien más sin necesitar saber de programación.
7. **[07-conceptos-teoricos.md](07-conceptos-teoricos.md)** — la teoría
   detrás de cada pieza usada en el proyecto (máquina de estados,
   detección de palabra de activación, sonido digital, reconocimiento
   de voz, modelos de lenguaje y de visión, síntesis de voz,
   concurrencia): qué es cada cosa y cómo funciona por dentro, a nivel
   intermedio.
8. **[08-exploracion-motor-de-voz.md](08-exploracion-motor-de-voz.md)** —
   la búsqueda de una voz en castellano más natural (XTTS-v2, MeloTTS,
   Chatterbox Multilingual + el checkpoint es-ES, Pocket TTS): qué se
   probó, qué bugs se encontraron y cómo se arreglaron, por qué ninguno
   se quedó como definitivo, y por qué BMO se queda con la voz de Piper
   original.

## Resumen en un párrafo

`agent.py` es una app de un solo archivo, hecha con Tkinter, que convierte
una Raspberry Pi + pantalla + micro + altavoz + cámara en un asistente
conversacional offline con una cara animada: detecta una palabra de
activación (openWakeWord), graba y transcribe tu voz (whisper.cpp), la
envía a un LLM local (Ollama, modelos de texto + visión), opcionalmente
llama a una de tres herramientas (reloj, búsqueda web en DuckDuckGo,
captura de cámara), y habla la respuesta en voz alta (Piper TTS) mientras
recorre fotogramas PNG de la cara según el estado
(idle/listening/thinking/speaking/error). Está pensado como un "lienzo en
blanco" — cambia los PNGs de la cara, los sonidos y el modelo de voz para
convertirlo en BMO.
