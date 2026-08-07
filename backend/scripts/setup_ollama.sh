#!/bin/bash
# Ollama Setup Script for Professional AI
# This script installs and configures Ollama with all required models
# Run this on the server (Google Cloud VM) before starting Docker

set -e

echo "========================================="
echo "Ollama Installation & Setup"
echo "========================================="

# Install Ollama
if ! command -v ollama &> /dev/null; then
    echo "Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
else
    echo "Ollama already installed"
fi

# Start Ollama service
echo "Starting Ollama service..."
sudo systemctl enable ollama
sudo systemctl start ollama

# Wait for Ollama to be ready
echo "Waiting for Ollama to be ready..."
sleep 5

# Pull all required models
echo "========================================="
echo "Pulling AI Models (this may take 10-30 minutes)"
echo "========================================="

# Primary models (70b-72b for best quality)
echo "Pulling llama3.1:70b..."
ollama pull llama3.1:70b

echo "Pulling qwen2.5:72b..."
ollama pull qwen2.5:72b

echo "Pulling deepseek-r1:70b..."
ollama pull deepseek-r1:70b

# Lightweight models for fast responses
echo "Pulling mistral..."
ollama pull mistral

echo "Pulling phi3..."
ollama pull phi3

echo "Pulling gemma2..."
ollama pull gemma2

# Create Modelfile for optimized chat
echo "========================================="
echo "Creating optimized model configurations"
echo "========================================="

mkdir -p ~/.ollama/models/professional-ai

# Create custom model for code generation
cat > ~/.ollama/models/professional-ai/Modelfile << 'EOF'
FROM llama3.1:70b

SYSTEM """You are a professional AI assistant specialized in:
- Code generation and debugging
- Technical documentation
- System architecture
- Cybersecurity analysis
- Business intelligence

Always provide accurate, well-structured responses with code examples when relevant.
"""

PARAMETER temperature 0.7
PARAMETER num_ctx 8192
PARAMETER top_p 0.9
EOF

# Create custom model for fast responses
cat > ~/.ollama/models/professional-ai/Modelfile-fast << 'EOF'
FROM mistral

SYSTEM """You are a fast, efficient AI assistant. Provide concise, accurate responses.
Best for quick questions, summaries, and simple tasks.
"""

PARAMETER temperature 0.5
PARAMETER num_ctx 4096
PARAMETER top_p 0.8
EOF

# Create custom model for reasoning
cat > ~/.ollama/models/professional-ai/Modelfile-reasoning << 'EOF'
FROM deepseek-r1:70b

SYSTEM """You are an advanced reasoning AI. Think step-by-step through complex problems.
Show your reasoning process clearly. Best for:
- Complex problem solving
- Mathematical proofs
- Logical analysis
- Deep technical questions
"""

PARAMETER temperature 0.3
PARAMETER num_ctx 16384
PARAMETER top_p 0.95
EOF

echo "========================================="
echo "Ollama Setup Complete!"
echo "========================================="
echo "Models installed:"
ollama list
echo ""
echo "Ollama API available at: http://localhost:11434"
echo "Test with: curl http://localhost:11434/api/generate -d '{\"model\": \"llama3.1:70b\", \"prompt\": \"Hello\"}'"
echo ""
echo "Next steps:"
echo "1. Update .env file with OLLAMA_BASE_URL=http://localhost:11434"
echo "2. Start Docker services: docker-compose up -d"
echo "3. Test the API: curl http://localhost:8000/api/health"