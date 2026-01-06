#!/data/data/com.termux/files/usr/bin/bash
# Installation script for Termux Login System

echo "=== INSTALLING TERMUX LOGIN SYSTEM ==="

# Update package list
pkg update -y

# Install Python jika belum ada
if ! command -v python3 &> /dev/null; then
    echo "Installing Python..."
    pkg install python -y
fi

# Buat direktori aplikasi
APP_DIR="$HOME/.termux_login"
mkdir -p $APP_DIR
cd $APP_DIR

# Salin file aplikasi
echo "Copying application files..."
cp /path/to/login_system.py ./

# Buat file executable
chmod +x login_system.py

# Buat alias untuk mudah diakses
echo "alias login='python $APP_DIR/login_system.py'" >> $HOME/.bashrc
echo "alias logout='exit'" >> $HOME/.bashrc

# Reload bashrc
source $HOME/.bashrc

echo "Installation complete!"
echo "Type 'login' to start the application"
