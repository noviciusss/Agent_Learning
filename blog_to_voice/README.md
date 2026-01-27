# blog_to_voice

Purpose

- Convert blog content into speech/audio files or generate spoken summaries.

Key files

- `agent.py` — main script. Inspect it to see how input is provided (URL, file, or raw text) and where outputs are written.
- `requirements.txt` — Python dependencies for this project.

Quick start (Windows)

```
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python agent.py
```

Configuration

- Check `agent.py` for options such as input sources, output directory, voice/TTS provider, and any API keys.
- If the script uses an external TTS service, set API keys as environment variables rather than committing them.

Expected outputs

- Audio files (e.g., MP3) or console/log output depending on how `agent.py` is configured.

