# Environment Variables

Create this file as `OpenEnvironment/server/.env`. At minimum, set one LLM API key.

```bash
# LLM API keys (at least one required)
CEREBRAS_API_KEY=your_key_here
# TOGETHER_API_KEY=your_key_here
# GEMINI_API_KEY=your_key_here

# LLM provider selection (default: cerebras)
# Options: cerebras, together, google
# LLM_PROVIDER=cerebras

# LLM model override
# Cerebras: llama3.1-8b, llama3.1-70b
# Together: meta-llama/Llama-3-8b-chat-hf
# Google: gemini-pro
# LLM_MODEL=llama3.1-8b

# Server
# PORT=8001
# DEBUG=false
# LOG_LEVEL=INFO

# Terrain defaults
# TERRAIN_RESOLUTION=512
# DEFAULT_SEED=42
```

Without any API key, the system uses regex-based parsing only. The provider cascade is Cerebras -> Together -> Gemini.

Never commit this file.
