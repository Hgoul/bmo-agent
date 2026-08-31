# Conceptos Teóricos Detrás de BMO

Este documento explica **la teoría** que hay detrás de cada pieza
tecnológica que usa el proyecto — no solo "qué programa instalamos",
sino "por qué existe ese tipo de programa y cómo funciona por dentro",
a un nivel intermedio (más técnico que
[06-explicacion-sencilla.md](06-explicacion-sencilla.md), pero sin
necesitar saber programar).

## 1. Máquina de estados (Finite State Machine)

**La idea:** un sistema que solo puede estar en **una situación
concreta a la vez**, de una lista cerrada de situaciones posibles, y
que salta de una a otra según lo que va pasando. Es como un semáforo:
solo puede estar en rojo, ámbar o verde — nunca "un poco de los dos" —
y pasa de uno a otro según reglas fijas.

**En BMO:** el bot solo puede estar en un estado de esta lista:
`IDLE` (esperando), `LISTENING` (escuchando), `THINKING` (pensando),
`SPEAKING` (hablando), `CAPTURING` (haciendo una foto), `ERROR`. Cada
estado tiene su propia carita animada. Pensar el programa como una
máquina de estados es lo que permite que la pantalla siempre sepa qué
dibujar sin tener que adivinar "¿qué está haciendo BMO ahora mismo?" —
siempre hay una única respuesta clara.

## 2. Detección de la palabra de activación (Wake Word Detection)

**La idea:** un programa pequeño y muy eficiente que escucha
**continuamente** el micrófono, pero solo está entrenado para
reconocer una cosa muy concreta (por ejemplo, "Hey Jarvis"), no para
entender lenguaje en general. Funciona comparando fragmentos cortos de
sonido (de menos de un segundo) contra el patrón que aprendió durante
su entrenamiento, y da una puntuación de "cuánto se parece" — si esa
puntuación supera un umbral, se activa.

Es la razón por la que este tipo de detección puede correr todo el
día sin gastar apenas batería/CPU: es mucho más simple que "entender lo
que dices", solo tiene que reconocer un sonido concreto, parecido a
cómo reconoces el timbre de tu propia puerta entre todos los ruidos de
la calle sin tener que "escuchar activamente" todo el rato.

**En BMO:** esto es `openWakeWord`. Analiza el audio del micrófono en
trocitos de 80 milisegundos, calcula una puntuación de "esto suena a
la palabra de activación" (entre 0 y 1), y cuando esa puntuación pasa
de 0.5, dispara el resto del proceso (grabar → transcribir → pensar →
hablar).

## 3. Sonido digital: muestreo, ganancia y saturación

Esto es la teoría detrás del problema del micrófono que resolvimos.

- **Muestreo (sample rate):** un micrófono no graba un sonido
  continuo de verdad — lo mide muchísimas veces por segundo y guarda
  cada medida como un número. "44100 Hz" significa que se toma una
  medida 44.100 veces por segundo. Cuantas más medidas por segundo, más
  fiel es la grabación al sonido real, pero también pesa más.
- **Ganancia (gain):** antes de guardar esas medidas, el sonido
  captado por el micrófono pasa por un "amplificador" que puede
  subirlo o bajarlo, igual que el volumen de un altavoz pero en
  sentido contrario (aquí amplifica lo que *entra*, no lo que *sale*).
- **Saturación (clipping):** cada medida solo puede guardarse dentro
  de un rango de números fijo (por ejemplo, de -32.768 a +32.767). Si
  la ganancia está demasiado alta, el sonido real "se sale" de ese
  rango y el programa lo recorta al valor máximo — el resultado es un
  chasquido/ruido duro en vez del sonido real, como una foto
  totalmente blanca de sobreexpuesta al sol.

**En BMO:** esto es exactamente lo que pasó — la ganancia del
micrófono estaba al máximo posible, cualquier sonido (incluida tu voz)
se salía del rango permitido, y el resultado era ruido saturado en vez
de una grabación limpia de tu voz. Bajar la ganancia devolvió el
sonido a un rango donde cabe sin recortarse.

## 4. Reconocimiento de voz (Speech-to-Text / ASR)

**La idea:** convertir una onda de sonido (tu voz) en texto escrito.
Por dentro, el programa no "escucha palabras" directamente — primero
convierte el audio en una especie de "foto" de cómo suena a lo largo
del tiempo y en distintas frecuencias (un *espectrograma*, algo así
como el ecualizador visual que se ve en algunos reproductores de
música), y luego una red neuronal entrenada con muchísimas horas de
voz humana transcrita va prediciendo, trozo a trozo, qué palabras
encajan con ese patrón.

**En BMO:** esto es `faster-whisper`, basado en el modelo Whisper.
Usamos la versión "base" del modelo (hay versiones más grandes y más
precisas, pero más lentas) y en modo "int8" — es decir, los cálculos
internos se hacen con números más simples/pequeños de lo habitual a
cambio de ir más rápido, perdiendo solo un poquito de precisión. Es un
intercambio razonable porque BMO necesita responder rápido, no
transcribir con precisión perfecta un audiolibro.

## 5. Modelos de lenguaje (LLM — Large Language Model)

**La idea:** un programa entrenado con enormes cantidades de texto que
aprende a predecir "cuál es la palabra más probable que sigue" dada
una conversación. No "sabe" cosas como una base de datos — genera
texto palabra a palabra (en realidad, en trocitos llamados *tokens*)
basándose en patrones aprendidos durante el entrenamiento. Cuando le
das una pregunta, no "busca la respuesta" en ningún sitio: la va
construyendo sobre la marcha, prediciendo el token más probable una y
otra vez.

**Modelo local vs. modelo en la nube:** ChatGPT vive en servidores de
OpenAI — cada vez que le escribes, tu mensaje viaja por internet hasta
allí y la respuesta vuelve. Un modelo *local* (como los que usa BMO)
es una versión mucho más pequeña que cabe y funciona enteramente
dentro de tu propio ordenador, sin mandar nada a ningún sitio — a
cambio de ser menos potente que los modelos gigantes de la nube, pero
gratis, privado, y funciona sin internet.

**En BMO:** `Ollama` es el programa que carga y ejecuta estos modelos
localmente. `gemma3:1b` es el modelo de texto ("1b" = mil millones de
parámetros, es decir, mil millones de "perillas" internas ajustadas
durante el entrenamiento — pequeño comparado con los modelos grandes
de la nube, que pueden tener cientos de miles de millones). Al modelo
también se le enseña, dentro de las instrucciones que recibe, que
puede "pedir usar una herramienta" (mirar la hora, buscar en internet,
hacer una foto) en vez de responder directamente — para eso, contesta
con una instrucción especial en vez de una frase normal, y el código
de `agent.py` reconoce esa instrucción y actúa en consecuencia.

## 6. Modelos de visión (Vision-Language Models)

**La idea:** una variante de los modelos de lenguaje que, además de
texto, puede recibir una **imagen** como parte de la pregunta. Por
dentro, la imagen se convierte también en una especie de "tokens"
(igual que las palabras), de forma que el mismo tipo de red neuronal
que predice texto palabra a palabra puede "razonar" sobre lo que hay
en la imagen y describirlo o responder preguntas sobre ella.

**En BMO:** `moondream` es el modelo de visión. Se usa solo cuando
BMO ha hecho una foto (con la cámara) — la imagen se manda junto con
la pregunta, y el modelo describe o responde sobre lo que "ve".

## 7. Síntesis de voz (Text-to-Speech / TTS)

**La idea:** el proceso contrario al reconocimiento de voz — convertir
texto escrito en una onda de sonido hablada. Primero el texto se
descompone en *fonemas* (los sonidos básicos del habla, como las
sílabas pero a nivel de sonido puro), y luego un modelo entrenado con
grabaciones de una voz humana genera el audio correspondiente a esos
fonemas, con una entonación lo más natural posible.

**En BMO:** esto es `Piper`. La "voz" que usa (el archivo
`.onnx`) es literalmente un modelo entrenado con grabaciones de una
persona real diciendo muchas frases — por eso puedes tener voces
distintas (inglesa, española, de hombre, de mujer...) simplemente
cambiando qué archivo de voz le pasas, sin cambiar el programa.

## 8. Concurrencia: hilos (threads)

**La idea:** normalmente un programa hace una cosa detrás de otra, en
orden. Pero algunas tareas necesitan pasar "en paralelo" — por
ejemplo, mientras BMO habla, la pantalla tiene que seguir animando la
boca, y a la vez tiene que poder detectar si le pulsas una tecla para
interrumpirlo. Un **hilo** es como una segunda persona trabajando a la
vez en el mismo proyecto: comparten la misma "mesa de trabajo"
(memoria), así que hay que tener cuidado de que no se estorben (por
ejemplo, que uno no borre algo que el otro está usando en ese
instante).

**En BMO:** hay varios hilos funcionando a la vez: uno dibuja la cara
y gestiona la ventana, otro escucha el micrófono y gestiona toda la
conversación, otro va reproduciendo las frases de la respuesta a
medida que están listas (para que BMO empiece a hablar sin esperar a
que el cerebro termine de pensar la frase entera), y otro reproduce
sonidos de "pensando" mientras espera al modelo de lenguaje.

## Cómo encajan todos estos conceptos en el flujo completo

```
Tu voz (sonido analógico)
   → muestreo digital (sección 3)
   → detección de palabra de activación (sección 2)
   → grabación
   → reconocimiento de voz: audio → texto (sección 4)
   → modelo de lenguaje: texto → respuesta o "usar herramienta" (sección 5)
        → (si hace falta ver algo) modelo de visión (sección 6)
   → síntesis de voz: respuesta → audio (sección 7)
   → todo esto coordinado en paralelo mediante hilos (sección 8)
   → y en todo momento, una máquina de estados (sección 1) decide qué cara mostrar
```

Ninguna de estas siete piezas es exclusiva de BMO — son bloques
genéricos que se usan en muchísimos productos de IA distintos (Alexa,
Siri, Google Assistant funcionan con las mismas ideas, aunque con sus
propios modelos y, en su caso, casi todo en la nube en vez de local).
Lo que hace especial a este proyecto es juntarlas todas para que
funcionen **enteramente dentro de un ordenador pequeño, sin depender
de internet**.
