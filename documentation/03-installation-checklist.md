# Checklist de Instalación (Raspberry Pi 5)

Pasos concretos y ordenados para conseguir una base *funcional* antes de
cualquier personalización específica de BMO. Se asume Raspberry Pi OS de
64 bits (Bookworm o posterior) en una Pi 5, con 8GB de RAM recomendados,
módulo de cámara y micro + altavoz USB (o I2S) conectados.

Los pasos marcados **[setup.sh]** ya están automatizados por el script de
este repo. Los pasos marcados **[MANUAL — falta en setup.sh]** no lo
están, y son necesarios para que el agente funcione siquiera (ver
[02-whats-missing.md](02-whats-missing.md)).

## 0. Requisitos a nivel de sistema operativo

```bash
sudo raspi-config
```
- Habilita la interfaz de cámara (Interface Options → Camera), o asegúrate
  de que `camera_auto_detect=1` esté puesto en
  `/boot/firmware/config.txt`.
- Reinicia después de habilitarla.

Verifica que el hardware se detecta de verdad antes de instalar nada más:

```bash
rpicam-hello --list-cameras          # cámara
arecord -l                           # micro (a nivel de ALSA)
python3 -c "import sounddevice as sd; print(sd.query_devices())"  # micro (a nivel de Python, tras el paso 5)
```

## 1. Paquetes del sistema — **[setup.sh]**

```bash
sudo apt update
sudo apt install -y python3-tk python3-dev libasound2-dev portaudio19-dev \
    liblapack-dev libblas-dev cmake build-essential espeak-ng git
```

`setup.sh` también crea la estructura de carpetas esperada
(`piper/`, `voices/`, `sounds/*`, `faces/*`).

## 2. Ollama + modelos

Instala Ollama (instalador oficial):

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Descarga los modelos que el código realmente usa (**no** la línea
`gemma:2b` del README actual — ver
[02-whats-missing.md](02-whats-missing.md) punto 2):

```bash
ollama pull gemma3:1b     # modelo de texto — coincide con config.json
ollama pull moondream     # modelo de visión — coincide con config.json
```

`setup.sh` hace esto automáticamente si `ollama` ya está en el `PATH`.

## 3. whisper.cpp — **[MANUAL — falta en setup.sh]**

Nada en este repo instala whisper.cpp, pero `agent.py` tiene una llamada a
él fija en el código. Compílalo desde el código fuente (rápido de
compilar, no necesita GPU):

```bash
git clone https://github.com/ggml-org/whisper.cpp.git
cd whisper.cpp
cmake -B build
cmake --build build --config Release -j4
# base.en da un buen equilibrio velocidad/precisión en la Pi 5; tiny.en es más rápido/menos preciso
bash ./models/download-ggml-model.sh base.en
cd ..
```

Coloca (o enlaza con symlink) el resultado para que las rutas que espera
`agent.py` se resuelvan desde la raíz del repo:

```
whisper.cpp/build/bin/whisper-cli
whisper.cpp/models/ggml-base.en.bin
```

Comprobación rápida:

```bash
./whisper.cpp/build/bin/whisper-cli -m ./whisper.cpp/models/ggml-base.en.bin -l en -t 4 -f some_test.wav
```

> Considera usar `faster-whisper` en su lugar — es un simple `pip install`,
> sin paso de compilación en C++, y normalmente es más rápido que
> whisper.cpp en la Pi 5 para los tamaños de modelo tiny/base. Ver
> [04-modernization-ideas.md](04-modernization-ideas.md) para las
> ventajas/desventajas y qué habría que cambiar en `agent.py`.

## 4. Piper TTS — **[setup.sh, solo aarch64]**

`setup.sh` descarga automáticamente una versión fija de Piper y la voz
`en_GB-semaine` por defecto **solo cuando se ejecuta en `aarch64`** (es
decir, en la Pi de verdad, no cuando pruebas setup.sh en otro sitio):

```bash
# gestionado por setup.sh en aarch64:
#   descarga piper_linux_aarch64.tar.gz en piper/
#   descarga en_GB-semaine-medium.onnx(.json) en piper/
```

Si usas la voz BMO personalizada, después de ejecutar `setup.sh`,
**corrige la discrepancia de nombre de archivo** (ver
[02-whats-missing.md](02-whats-missing.md) punto 3) antes de apuntar
`config.json` a ella:

```bash
ls voices/          # confirma los nombres de archivo realmente descargados
# luego pon "voice_model" en config.json para que coincida exactamente, p. ej.:
#   "voices/bmo-custom.onnx"
```

Prueba Piper por separado antes de integrarlo en la app completa:

```bash
echo "Hello, I am BMO." | ./piper/piper --model piper/en_GB-semaine-medium.onnx --output_file test.wav
aplay test.wav
```

## 5. Entorno Python

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install --force-reinstall --no-cache-dir sounddevice   # re-enlazar contra portaudio19-dev
pip install -r requirements.txt
```

(`setup.sh` también hace todo esto.)

## 6. Palabra de activación

Por defecto (funciona de inmediato, pero dice "Hey Jarvis", no "BMO"):

```bash
curl -L -o wakeword.onnx https://github.com/dscripka/openWakeWord/raw/main/openwakeword/resources/models/hey_jarvis_v0.1.onnx
```

Para conseguir una palabra de activación real de "Hey BMO", entrena un
modelo personalizado (proceso aparte, manual, de una sola vez — no es algo
que `setup.sh` pueda automatizar porque necesita tus propias muestras
grabadas/sintetizadas):

1. Sigue el notebook de entrenamiento de openWakeWord:
   https://github.com/dscripka/openWakeWord
2. Exporta el archivo `.onnx` resultante.
3. Sustituye `wakeword.onnx` en la raíz del repo por él.

**Nota específica de la Pi:** openWakeWord puede funcionar tanto con
backend ONNX como TFLite. `tflite-runtime` tiene un historial documentado
de romperse en las wheels ARM de la Pi; si te encuentras con errores de
instalación en `openwakeword`, fuerza explícitamente el backend ONNX en
lugar de pelearte con `tflite-runtime` — ver
[04-modernization-ideas.md](04-modernization-ideas.md).

## 7. Primera ejecución (manual, en primer plano, antes de configurar el autoarranque)

```bash
source venv/bin/activate
python agent.py
```

Vigila la consola — la mayoría de fallos (binario de whisper ausente,
nombre de modelo de Ollama incorrecto, archivo de voz ausente, cámara no
encontrada) imprimen un mensaje antes de volver en silencio a
`IDLE`/`ERROR` en la interfaz gráfica.

## 8. Autoarranque al iniciar (una vez el paso 7 funcione de forma fiable)

El repo incluye un lanzador `.desktop` (`be-more-agent.desktop`) pensado
para un flujo de sesión de escritorio + clic en icono — edita sus rutas
`Exec`/`Path`/`Icon` para que coincidan con dónde clonaste realmente el
repo y cuál es el nombre de usuario de la Pi (ver
[02-whats-missing.md](02-whats-missing.md) punto 8).

Para un BMO físico sellado sin interacción de escritorio, un servicio
`systemd` es más robusto (se reinicia solo si falla, arranca antes de
cualquier login):

```ini
# /etc/systemd/system/bmo-agent.service
[Unit]
Description=BMO AI Agent
After=network.target sound.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/be-more-agent
ExecStart=/home/pi/be-more-agent/start_agent.sh
Restart=on-failure
RestartSec=3

[Install]
WantedBy=graphical.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now bmo-agent.service
journalctl -u bmo-agent -f   # ver los logs en vez de una ventana de consola
```

## Referencia rápida: qué espera encontrar en disco cada campo de config

| Campo de `config.json` | Debe existir en |
|---|---|
| (fijo en el código) | `whisper.cpp/build/bin/whisper-cli`, `whisper.cpp/models/ggml-base.en.bin` |
| `voice_model` | p. ej. `piper/en_GB-semaine-medium.onnx` o `voices/bmo-custom.onnx`, **y** su `.onnx.json` correspondiente al lado |
| (fijo en el código) | binario `./piper/piper` |
| (fijo en el código) | `./wakeword.onnx` |
| `text_model` / `vision_model` | deben ser visibles en `ollama list` (es decir, ya descargados) |
