# ai_flask_api

Install ollama and flask, python library to start the server

## Install OLLAMA

```
pip install ollama
```

## Install Flask

```
pip install flask
```

# Ollama Configuration

Pull Ollama model to use in flask API

```
ollama pull <model-name>
```
for eg:) 

```
ollama pull llama3.2:latest
```

```
ollama pull qwen3:0.6b
```

To start ollama

```
ollama start <model-name>
```

To stop ollama

```
ollama stop <model-name>
```
