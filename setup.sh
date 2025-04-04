#!/bin/bash

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if running on Arch Linux
is_arch() {
    [ -f "/etc/arch-release" ]
}

# Function to check if running on Ubuntu/Debian
is_debian() {
    [ -f "/etc/debian_version" ]
}

# Function to check if running on Fedora
is_fedora() {
    [ -f "/etc/fedora-release" ]
}

echo "Checking system dependencies..."

# Check Python
if ! command_exists python; then
    echo "Python not found. Installing..."
    if is_arch; then
        sudo pacman -S python
    elif is_debian; then
        sudo apt-get update && sudo apt-get install -y python3
    elif is_fedora; then
        sudo dnf install -y python3
    else
        echo "Unsupported distribution. Please install Python manually."
        exit 1
    fi
fi

# Check pip
if ! command_exists pip; then
    echo "pip not found. Installing..."
    if is_arch; then
        sudo pacman -S python-pip
    elif is_debian; then
        sudo apt-get update && sudo apt-get install -y python3-pip
    elif is_fedora; then
        sudo dnf install -y python3-pip
    else
        echo "Unsupported distribution. Please install pip manually."
        exit 1
    fi
fi

# Check Docker
if ! command_exists docker; then
    echo "Docker not found. Installing..."
    if is_arch; then
        sudo pacman -S docker
    elif is_debian; then
        sudo apt-get update
        sudo apt-get install -y ca-certificates curl gnupg
        sudo install -m 0755 -d /etc/apt/keyrings
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
        sudo chmod a+r /etc/apt/keyrings/docker.gpg
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
        sudo apt-get update
        sudo apt-get install -y docker-ce docker-ce-cli containerd.io
    elif is_fedora; then
        sudo dnf -y install dnf-plugins-core
        sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo
        sudo dnf install -y docker-ce docker-ce-cli containerd.io
    else
        echo "Unsupported distribution. Please install Docker manually."
        exit 1
    fi
fi

# Check Docker Compose
if ! command_exists docker-compose; then
    echo "Docker Compose not found. Installing..."
    if is_arch; then
        sudo pacman -S docker-compose
    elif is_debian; then
        sudo apt-get update && sudo apt-get install -y docker-compose
    elif is_fedora; then
        sudo dnf install -y docker-compose
    else
        echo "Unsupported distribution. Please install Docker Compose manually."
        exit 1
    fi
fi

# Start Docker service if not running
if ! systemctl is-active --quiet docker; then
    echo "Starting Docker service..."
    sudo systemctl start docker
fi

# Add current user to docker group if not already in it
if ! groups | grep -q docker; then
    echo "Adding user to docker group..."
    sudo usermod -aG docker $USER
    echo "Please log out and back in for docker group changes to take effect."
fi

# Create Python virtual environment and install requirements
echo "Setting up Python virtual environment..."
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

echo "Setup complete! Please log out and back in if you were added to the docker group."
echo "To start the agent, run: source venv/bin/activate && ./local_agent.py" 