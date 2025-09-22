#!/bin/bash

# Air Quality Monitor Installation Script for Raspberry Pi
# Run with: chmod +x install.sh && ./install.sh

set -e

echo "=========================================="
echo "🌬️  Air Quality Monitor Setup"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on Raspberry Pi
if ! cat /proc/cpuinfo | grep -q "Raspberry Pi"; then
    print_warning "This script is designed for Raspberry Pi. Proceeding anyway..."
fi

# Update system
print_status "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install system dependencies
print_status "Installing system dependencies..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    git \
    i2c-tools \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libopenjp2-7 \
    libtiff5 \
    build-essential

# Enable I2C and SPI
print_status "Configuring GPIO interfaces..."
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_spi 0

# Configure UART
print_status "Configuring UART..."
if ! grep -q "enable_uart=1" /boot/config.txt; then
    echo "enable_uart=1" | sudo tee -a /boot/config.txt
fi

# Add UART overlays if not present
if ! grep -q "dtoverlay=uart2" /boot/config.txt; then
    echo "dtoverlay=uart2" | sudo tee -a /boot/config.txt
fi

if ! grep -q "dtoverlay=uart3" /boot/config.txt; then
    echo "dtoverlay=uart3" | sudo tee -a /boot/config.txt
fi

# Create project directory
PROJECT_DIR="$HOME/air-quality-monitor"
if [ ! -d "$PROJECT_DIR" ]; then
    print_status "Creating project directory: $PROJECT_DIR"
    mkdir -p "$PROJECT_DIR"
fi

cd "$PROJECT_DIR"

# Create virtual environment
print_status "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
print_status "Installing Python packages..."
pip install --upgrade pip

# Install packages one by one to handle potential failures
packages=(
    "pyserial>=3.5"
    "RPi.GPIO>=0.7.1"
    "spidev>=3.5"
    "adafruit-circuitpython-dht>=3.7.0"
    "adafruit-circuitpython-sgp30>=2.3.0"
    "adafruit-circuitpython-ssd1306>=2.12.0"
    "adafruit-blinka>=8.0.0"
    "Pillow>=9.0.0"
    "Flask>=2.3.0"
    "Flask-SocketIO>=5.3.0"
    "plotly>=5.15.0"
    "pandas>=1.5.0"
    "numpy>=1.24.0"
)

for package in "${packages[@]}"; do
    print_status "Installing $package..."
    if pip install "$package"; then
        print_success "Successfully installed $package"
    else
        print_error "Failed to install $package"
    fi
done

# Set up user permissions
print_status "Setting up user permissions..."
sudo usermod -a -G dialout,gpio,i2c,spi $USER

# Create systemd service file
print_status "Creating systemd service..."
sudo tee /etc/systemd/system/airiq.service > /dev/null <<EOF
[Unit]
Description=Air Quality Monitor
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python AirIQ.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create systemd service for web dashboard
print_status "Creating web dashboard service..."
sudo tee /etc/systemd/system/airiq-web.service > /dev/null <<EOF
[Unit]
Description=Air Quality Monitor Web Dashboard
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python web_dashboard.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
sudo systemctl daemon-reload

# Create startup script
print_status "Creating startup script..."
tee start_monitor.sh > /dev/null <<EOF
#!/bin/bash
cd $PROJECT_DIR
source venv/bin/activate
python3 AirIQ.py
EOF

chmod +x start_monitor.sh

# Create web dashboard startup script
tee start_web.sh > /dev/null <<EOF
#!/bin/bash
cd $PROJECT_DIR
source venv/bin/activate
python3 web_dashboard.py
EOF

chmod +x start_web.sh

# Test I2C
print_status "Testing I2C interface..."
if command -v i2cdetect >/dev/null 2>&1; then
    i2cdetect -y 1 || print_warning "No I2C devices detected"
else
    print_warning "i2cdetect not available"
fi

# Test GPIO
print_status "Testing GPIO access..."
if [ -c /dev/gpiomem ]; then
    print_success "GPIO access available"
else
    print_warning "GPIO access may be limited"
fi

# Final instructions
echo ""
echo "=========================================="
print_success "Installation completed!"
echo "=========================================="
echo ""
echo "📝 Next steps:"
echo "1. Reboot your Raspberry Pi: sudo reboot"
echo "2. Connect your sensors according to the wiring diagram"
echo "3. Test the installation:"
echo "   cd $PROJECT_DIR"
echo "   source venv/bin/activate"
echo "   python3 AirIQ.py"
echo ""
echo "🌐 To start the web dashboard:"
echo "   python3 web_dashboard.py"
echo "   Then visit: http://$(hostname -I | cut -d' ' -f1):5000"
echo ""
echo "🚀 To enable auto-start on boot:"
echo "   sudo systemctl enable airiq.service"
echo "   sudo systemctl enable airiq-web.service"
echo ""
echo "📋 Configuration file: $PROJECT_DIR/config.json"
echo "📊 Data file: $PROJECT_DIR/air_quality_data.csv"
echo "📖 Full documentation: $PROJECT_DIR/README.md"
echo ""
echo "⚠️  Remember to reboot before connecting sensors!"

# Ask about reboot
echo ""
read -p "Would you like to reboot now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Rebooting in 5 seconds..."
    sleep 5
    sudo reboot
fi

print_success "Setup script completed successfully!"