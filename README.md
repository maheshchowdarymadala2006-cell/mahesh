# Local Chat

A lightweight browser chat interface for a local Ollama model. By default, it connects to Ollama at `http://localhost:11434` using `qwen2.5:3b`.

## Run on Windows

1. Make sure Ollama is running and the model is available: `ollama list`
2. Open PowerShell in this folder and run:

   ```powershell
   py -3 server.py
   ```

   If the Python launcher is unavailable, use `python server.py`.
3. Open [http://localhost:8000](http://localhost:8000) in your browser.
4. Stop the server with `Ctrl+C`.

No extra Python packages or Node.js are needed.

## Configuration

To use another Ollama host or model, set environment variables before starting the server:

```powershell
$env:OLLAMA_URL = "http://localhost:11434"
$env:OLLAMA_MODEL = "qwen2.5:3b"
py -3 server.py
```

If you change `OLLAMA_MODEL`, make sure that model is already installed in Ollama.
