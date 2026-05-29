#!/bin/bash
# Deploy Block 1 to DGX

# Configuration
DGX_HOST=${1:-localhost}
DGX_USER=${2:-root}
REPO_PATH=$(pwd)

echo "Deploying Block 1 to DGX..."
echo "DGX: $DGX_HOST"
echo "User: $DGX_USER"
echo "Local path: $REPO_PATH"

# 1. Copy repository to DGX
echo ""
echo "1. Copying repository to DGX..."
ssh $DGX_USER@$DGX_HOST "mkdir -p ~/Chat2Plan"
scp -r $REPO_PATH/* $DGX_USER@$DGX_HOST:~/Chat2Plan/

# 2. Install dependencies on DGX
echo ""
echo "2. Installing dependencies on DGX..."
ssh $DGX_USER@$DGX_HOST "cd ~/Chat2Plan && pip install -r requirements.txt"

# 3. Create .env on DGX
echo ""
echo "3. Setting up environment on DGX..."
ssh $DGX_USER@$DGX_HOST "cd ~/Chat2Plan && cp .env.example .env"
echo "   Please edit .env on DGX with correct values"
echo "   SSH in and run: nano ~/Chat2Plan/.env"

# 4. Create systemd service (optional)
echo ""
echo "4. Creating systemd service (optional)..."
ssh $DGX_USER@$DGX_HOST << 'EOF'
cat > /tmp/block1-api.service << 'SERVICE'
[Unit]
Description=Block 1 Research Ideation API
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/home/$USER/Chat2Plan
ExecStart=/usr/bin/python3 -m src.api_server
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE

echo "Service file created at /tmp/block1-api.service"
echo "To install: sudo cp /tmp/block1-api.service /etc/systemd/system/"
echo "Then: sudo systemctl daemon-reload && sudo systemctl enable block1-api"
EOF

echo ""
echo "Deployment complete!"
echo ""
echo "Next steps on DGX:"
echo "1. Edit .env: ssh $DGX_USER@$DGX_HOST 'nano ~/Chat2Plan/.env'"
echo "2. Start API server: ssh $DGX_USER@$DGX_HOST 'cd ~/Chat2Plan && python -m src.api_server'"
echo "3. Start file watcher: ssh $DGX_USER@$DGX_HOST 'cd ~/Chat2Plan && python -m src.file_watcher'"
