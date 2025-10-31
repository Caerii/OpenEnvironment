#!/bin/bash
# Bash script to start the frontend dev server (macOS/Linux)

echo "Starting Semantic Terrain Frontend..."

cd web

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Check if textures exist
textures=("grass.jpg" "rock.jpg" "sand.jpg" "snow.jpg")
missing=()
for tex in "${textures[@]}"; do
    if [ ! -f "public/textures/$tex" ]; then
        missing+=("$tex")
    fi
done

if [ ${#missing[@]} -gt 0 ]; then
    echo ""
    echo "WARNING: Missing texture files in web/public/textures/:"
    for tex in "${missing[@]}"; do
        echo "  - $tex"
    done
    echo ""
    echo "See web/public/textures/README.md for instructions."
    echo ""
fi

# Start dev server
echo "Starting Vite dev server on http://localhost:5173"
echo "Press Ctrl+C to stop"
npm run dev

