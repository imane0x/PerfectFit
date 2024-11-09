#!/bin/bash

# Install Ollama
curl https://ollama.ai/install.sh | sh
# Start the Ollama server in the background
ollama serve &

# Pull the 'llava' model for Ollama
ollama pull llava