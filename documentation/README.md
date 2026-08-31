# BMO Project Documentation

*[Leer esto en español](README.es.md)*

This folder documents the `be-more-agent` codebase as it currently sits in this
repo, before any of it has been deployed to the Raspberry Pi 5. It was written
to get us from "here's some code someone else wrote" to "we understand it well
enough to build BMO on top of it."

Read in this order:

1. **[01-code-walkthrough.md](01-code-walkthrough.md)** — what the code
   actually does today: architecture, state machine, the flow from wake word
   to spoken answer, file by file.
2. **[02-whats-missing.md](02-whats-missing.md)** — why `python agent.py`
   will **not** work out of the box, even after `setup.sh`. Bugs,
   inconsistencies, and unfinished pieces, ranked by how badly they block a
   first run.
3. **[03-installation-checklist.md](03-installation-checklist.md)** — the
   concrete, ordered list of things to install on the Pi 5 (system packages,
   Ollama + models, whisper.cpp, Piper, wake word) to get a working baseline,
   including the steps `setup.sh` is missing.
4. **[04-modernization-ideas.md](04-modernization-ideas.md)** — optional
   upgrades: components that work today but have better/faster/more current
   alternatives as of mid-2026, plus a sketch for adding actual voice
   (speaker) recognition, which the current code does not have at all.
5. **[05-estado-actual-ubuntu.md](05-estado-actual-ubuntu.md)** (Spanish) —
   summary of this Ubuntu-laptop development phase: code changes applied on
   top of the original, everything installed (and why those versions), and
   a microphone gain issue that came up and got fixed along the way.

## One-paragraph summary

`agent.py` is a single-file Tkinter app that turns a Raspberry Pi + screen +
mic + speaker + camera into an offline conversational assistant with an
animated face: it detects a wake word (openWakeWord), records and transcribes
your speech (whisper.cpp), sends it to a local LLM (Ollama, text + vision
models), optionally calls one of three tools (clock, DuckDuckGo web search,
camera capture), and speaks the reply back (Piper TTS) while cycling through
PNG face frames per state (idle/listening/thinking/speaking/error). It's
designed as a "blank canvas" — swap the face PNGs, the sounds, and the voice
model to reskin it as BMO.
