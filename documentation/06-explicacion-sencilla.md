# BMO Explicado de Forma Sencilla

Esta página explica el proyecto sin palabras técnicas, pensada para
poder contárselo a alguien más (o repasarlo tú mismo) sin necesitar
saber de programación.

## ¿Qué es BMO?

BMO es un robot/asistente casero, como Alexa o Siri, pero con una
diferencia importante: **todo el "cerebro" vive dentro del propio
aparato**, no en internet. No necesita mandar tus datos a ningún
servidor de Google ni de nadie — todo pasa dentro de la máquina.
Además tiene una pantalla con una carita animada (como el personaje
BMO de Hora de Aventura) que reacciona según lo que está haciendo.

## ¿Cómo funciona? (como una conversación)

Imagina que BMO tiene 4 partes, como una persona:

1. **Oídos** — un micrófono que te escucha.
2. **Un traductor** — convierte lo que dijiste (sonido) en texto
   escrito, como cuando el móvil transcribe un audio de WhatsApp.
3. **Un cerebro pequeñito** — una inteligencia artificial (parecida a
   ChatGPT pero mini y que vive dentro del ordenador, sin internet)
   que lee ese texto y piensa qué responder.
4. **Una boca** — convierte la respuesta (texto) otra vez en voz y la
   dice por el altavoz.

Y mientras todo esto pasa, la carita en la pantalla cambia: cara de
"esperando", cara de "te estoy escuchando", cara de "pensando", cara
de "hablando".

## ¿Por qué probamos esto en un portátil y no en el robot BMO de verdad?

BMO de verdad va a vivir dentro de una **Raspberry Pi** — es como un
ordenador diminuto, del tamaño de una tarjeta de crédito, que va
dentro del muñeco. El problema es que ese ordenador pequeño es lento y
más difícil de manejar mientras estamos arreglando cosas.

Es como cuando pruebas una receta nueva en tu cocina de casa antes de
hacerla en un restaurante con prisa: primero la dejamos perfecta aquí
en el portátil (que es rápido y fácil), y cuando todo funcione bien,
la pasamos al ordenador pequeño que va dentro de BMO.

## ¿Qué hemos instalado y arreglado?

- **El cerebro (Ollama)**: instalamos el programa que hace de "IA
  local" y le dimos dos "cerebros" descargados: uno para hablar normal
  (`gemma3`) y otro que puede "ver" fotos (`moondream`).
- **El traductor de voz a texto (faster-whisper)**: el programa que
  escucha lo que dices y lo convierte en texto.
- **La voz (Piper)**: el programa que convierte el texto de la
  respuesta en un audio hablado.
- **Arreglamos varias cositas rotas** del código que nos dieron: por
  ejemplo, el sonido de error nunca sonaba, y usaba una herramienta de
  búsqueda web que ya estaba desactualizada — las actualizamos.

## ¿Qué cambiamos del código original que nos dieron?

El código que recibimos ya traía la idea general montada, pero tenía
varias piezas rotas o a medio hacer — como recibir un mueble de IKEA
al que le faltan un par de tornillos y las instrucciones de una pieza
están mal impresas. Esto es lo que arreglamos:

- **El "traductor" de voz a texto no venía instalado.** El código
  original esperaba un programa (whisper.cpp) que había que construir
  a mano, con pasos complicados, y ese programa ni siquiera estaba
  incluido — así que, tal cual venía, BMO nunca llegaba a entender
  nada de lo que le decías (siempre "oía" silencio). Lo cambiamos por
  otro programa que hace lo mismo pero mucho más fácil de instalar
  (`faster-whisper`), como cambiar "monta este mueble con 40 pasos" por
  "este otro viene ya montado, solo hay que enchufarlo".
- **El sonido de error nunca sonaba.** Cuando algo fallaba, la carita
  de BMO se ponía en modo "error", pero no hacía ningún sonido — el
  aviso sonoro estaba preparado pero nunca se conectó. Lo conectamos,
  así que ahora si algo va mal, además de la cara también lo oyes.
- **La herramienta de búsqueda en internet estaba anticuada.** El
  programa que usaba BMO para buscar cosas en la web había cambiado de
  nombre (el que hacía la mismo lo siguen manteniendo, pero con otra
  etiqueta) y el código todavía llamaba al nombre viejo, que tarde o
  temprano iba a dejar de funcionar. Lo actualizamos al nombre nuevo.
- **La voz apuntaba a un archivo que no existía.** La configuración le
  decía a BMO "usa este archivo de voz" pero ese archivo, tal cual
  venía todo, nunca se llegaba a descargar con ese nombre exacto — como
  si en una receta pusiera "usa el bote azul" pero el bote se llame en
  realidad "bote celeste". Corregimos el nombre para que apunten al
  mismo archivo.

Lo que **no** hemos tocado todavía porque solo hace falta cuando BMO
esté dentro del muñeco de verdad: la cámara (sigue esperando la cámara
específica de la Raspberry Pi, que aquí en el portátil no existe) y la
palabra mágica para despertarlo (por ahora sigue siendo "Hey Jarvis",
todavía no le hemos enseñado a responder a "Hey BMO").

## El problema raro del micrófono (ya resuelto)

Cuando probamos a hablarle a BMO, en vez de escucharte bien, el
micrófono grababa solo **ruido y estática muy fuerte**, como una radio
mal sintonizada.

La causa: el micrófono del portátil tenía el "volumen de entrada"
puesto al máximo posible, como si le hubieras subido el volumen de un
altavoz hasta el tope — en vez de escuchar tu voz con claridad, se
saturaba con cualquier ruidito de la habitación. Bajamos ese volumen a
un nivel normal, y ahora te escucha perfectamente.

## ¿Cómo va todo ahora?

✅ BMO ya te escucha, entiende lo que dices, piensa una respuesta, y la
dice en voz alta, con la carita animándose.

Lo que falta:

- 📷 Que pueda "ver" con una cámara — como no hay cámara en el
  portátil, hay que inventar una foto de prueba mientras tanto.
- 🖥️ Mudarlo todo al ordenador pequeño (Raspberry Pi) que va dentro
  del muñeco de verdad.

## Para saber más (versión técnica)

Si necesitas los detalles técnicos de todo esto — nombres exactos de
programas, versiones, comandos usados — están en
[05-estado-actual-ubuntu.md](05-estado-actual-ubuntu.md).
