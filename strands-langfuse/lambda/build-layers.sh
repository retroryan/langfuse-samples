#!/bin/bash
set -e

echo "🏗️  Building Lambda layers with Docker for x86_64 architecture..."

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LAYERS_DIR="$SCRIPT_DIR/layers"
BUILD_DIR="$SCRIPT_DIR/build"

# Clean previous builds
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Function to build a layer
build_layer() {
    local layer_name=$1
    local layer_dir=$2
    
    echo "📦 Building $layer_name layer..."
    
    # Create layer structure
    mkdir -p "$BUILD_DIR/$layer_name/python"
    
    # Use Docker to install dependencies
    docker run --rm \
        --platform linux/amd64 \
        -v "$layer_dir:/var/task" \
        -v "$BUILD_DIR/$layer_name/python:/var/task/python" \
        --entrypoint /bin/bash \
        public.ecr.aws/lambda/python:3.12 \
        -c "pip install -r /var/task/requirements.txt -t /var/task/python --upgrade"
    
    # Create zip
    cd "$BUILD_DIR/$layer_name"
    zip -r "../${layer_name}.zip" python/
    cd -
    
    echo "✅ Built $layer_name layer: $BUILD_DIR/${layer_name}.zip"
}

# Build layers
build_layer "base-deps-layer" "$LAYERS_DIR/base-deps"
build_layer "strands-layer" "$LAYERS_DIR/strands-layer"

# Package function code
echo "📦 Packaging function code..."
mkdir -p "$BUILD_DIR/function"
# Copy lambda handler
cp "$SCRIPT_DIR/lambda_handler.py" "$BUILD_DIR/function/"
# Copy core and demos from parent directory
cp -r "$SCRIPT_DIR/../core" "$BUILD_DIR/function/"
cp -r "$SCRIPT_DIR/../demos" "$BUILD_DIR/function/"
cd "$BUILD_DIR/function"
zip -r "../function-code.zip" .
cd -

echo "✅ All layers and function code built successfully!"
echo "📍 Build artifacts in: $BUILD_DIR"