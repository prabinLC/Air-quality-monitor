# AirIQ - DIY Air Quality Monitor v1.0

A comprehensive air quality monitoring system for Raspberry Pi that tracks PM2.5, CO2, VOC, Ozone, Temperature, and Humidity levels with web dashboard and data logging.

## 🚀 Quick Start

### 🎯 Recommended: Smart Launcher (Auto-detects Platform)
```bash
python start_airiq.py
```
*Automatically runs the right version based on your system*

### 🌐 Web Dashboard (Run in separate terminal)
```bash
python ultra_simple_web_dashboard.py
# Then visit: http://localhost:5000
```

### 📱 Manual Options
```bash
# For Raspberry Pi with real sensors
python AirIQ.py

# For testing/demo on any platform  
python AirIQ_demo.py
```

## ✨ Features

- **🔄 Multi-sensor monitoring**: PM2.5, PM10, CO2, VOC, Ozone, Temperature, Humidity
- **📺 Real-time display**: Console output with emojis and optional OLED display
- **📊 Data logging**: CSV file with timestamps for historical analysis
- **🌐 Web dashboard**: Beautiful responsive interface with real-time updates
- **🚨 Alert system**: Configurable thresholds for dangerous air quality levels
- **📈 Air Quality Index (AQI)**: Automatic calculation with color-coded categories
- **🎮 Demo mode**: Full simulation for testing without hardware
- **🚀 Smart launcher**: Auto-detects platform and runs appropriate version

## 📁 Project Structure

```
AirIQ/
├── 🎯 AirIQ.py                     # Main production monitor (Raspberry Pi)
├── 🎮 AirIQ_demo.py               # Demo version (Any platform)  
├── 🚀 start_airiq.py              # Smart launcher (Auto-detects platform)
├── 🌐 ultra_simple_web_dashboard.py # Web dashboard server
├── 📱 templates/
│   └── ultra_simple_dashboard.html # Web interface
├── ⚙️ config.json                 # Configuration file
├── 📊 air_quality_data.csv        # Data log (auto-generated)
├── 📦 requirements.txt            # Python dependencies
├── 🔧 install.sh                  # Raspberry Pi installer
├── 📖 README.md                   # This documentation
├── 📝 airiq.log                   # Runtime logs (auto-generated)
└── 🐍 .venv/                      # Python virtual environment
```

### 🎯 File Purposes
- **`AirIQ.py`** - Production version with real sensor hardware integration
- **`AirIQ_demo.py`** - Cross-platform demo with realistic sensor simulation
- **`start_airiq.py`** - Intelligent launcher that chooses the right version
- **`ultra_simple_web_dashboard.py`** - Flask web server for browser interface
- **`config.json`** - Sensor configuration and system settings

## Hardware Requirements

### Core Components
- **Raspberry Pi 4B** (or compatible)
- **MicroSD card** (32GB+ recommended)
- **Power supply** (5V 3A for Pi 4)

### Sensors
1. **PMS5003** - PM2.5/PM10 Particulate Matter Sensor
2. **MH-Z19** - CO2 Sensor (NDIR)
3. **SGP30** - VOC and eCO2 Sensor (I2C)
4. **MQ131** - Ozone Sensor (Analog)
5. **DHT22** - Temperature and Humidity Sensor
6. **MCP3008** - ADC for analog sensors (SPI)

### Optional Components
- **SSD1306 OLED Display** (128x64, I2C)
- **Breadboard and jumper wires**
- **Enclosure** for protection

## Wiring Diagram

### Raspberry Pi GPIO Pinout Reference
```
     3V3  (1) (2)  5V
   GPIO2  (3) (4)  5V
   GPIO3  (5) (6)  GND
   GPIO4  (7) (8)  GPIO14
     GND  (9) (10) GPIO15
  GPIO17 (11) (12) GPIO18
  GPIO27 (13) (14) GND
  GPIO22 (15) (16) GPIO23
     3V3 (17) (18) GPIO24
  GPIO10 (19) (20) GND
   GPIO9 (21) (22) GPIO25
  GPIO11 (23) (24) GPIO8
     GND (25) (26) GPIO7
   GPIO0 (27) (28) GPIO1
   GPIO5 (29) (30) GND
   GPIO6 (31) (32) GPIO12
  GPIO13 (33) (34) GND
  GPIO19 (35) (36) GPIO16
  GPIO26 (37) (38) GPIO20
     GND (39) (40) GPIO21
```

### Sensor Connections

#### PMS5003 (UART)
```
PMS5003    →  Raspberry Pi
VCC        →  5V (Pin 2)
GND        →  GND (Pin 6)
TX         →  GPIO15 (Pin 10) - RX
RX         →  GPIO14 (Pin 8) - TX
```

#### MH-Z19 (UART)
```
MH-Z19     →  Raspberry Pi
VCC        →  5V (Pin 4)
GND        →  GND (Pin 14)
TX         →  GPIO17 (Pin 11)
RX         →  GPIO18 (Pin 12)
```

#### SGP30 (I2C)
```
SGP30      →  Raspberry Pi
VCC        →  3.3V (Pin 1)
GND        →  GND (Pin 9)
SDA        →  GPIO2 (Pin 3) - SDA
SCL        →  GPIO3 (Pin 5) - SCL
```

#### DHT22 (Digital)
```
DHT22      →  Raspberry Pi
VCC        →  3.3V (Pin 17)
GND        →  GND (Pin 20)
DATA       →  GPIO4 (Pin 7)
```

#### MQ131 + MCP3008 (SPI/ADC)
```
MCP3008    →  Raspberry Pi
VDD        →  3.3V (Pin 1)
VREF       →  3.3V (Pin 1)
AGND       →  GND (Pin 6)
DGND       →  GND (Pin 6)
CLK        →  GPIO11 (Pin 23) - SCLK
DOUT       →  GPIO9 (Pin 21) - MISO
DIN        →  GPIO10 (Pin 19) - MOSI
CS         →  GPIO8 (Pin 24) - CE0

MQ131      →  MCP3008
VCC        →  3.3V
GND        →  GND
AOUT       →  CH0 (Pin 1)
```

#### SSD1306 OLED (Optional, I2C)
```
SSD1306    →  Raspberry Pi
VCC        →  3.3V (Pin 17)
GND        →  GND (Pin 25)
SDA        →  GPIO2 (Pin 3) - SDA
SCL        →  GPIO3 (Pin 5) - SCL
```

## Software Installation

### 1. Prepare Raspberry Pi

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3 and pip
sudo apt install python3 python3-pip python3-venv git -y

# Enable I2C and SPI
sudo raspi-config
# Navigate to: Interface Options → I2C → Enable
# Navigate to: Interface Options → SPI → Enable
# Reboot when prompted
```

### 2. Clone and Setup Project

```bash
# Clone or download the AirIQ project
git clone <repository-url>
cd AirIQ

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Test installation with demo
python start_airiq.py
```

### 3. Configure UART (for PMS5003 and MH-Z19)

```bash
# Edit boot config
sudo nano /boot/config.txt

# Add these lines:
enable_uart=1
dtoverlay=uart2
dtoverlay=uart3
dtoverlay=uart4
dtoverlay=uart5

# Edit cmdline
sudo nano /boot/cmdline.txt
# Remove: console=serial0,115200

# Reboot
sudo reboot
```

### 4. Test Installation

```bash
# Test I2C devices
i2cdetect -y 1

# Test UART ports
ls /dev/ttyUSB* /dev/ttyAMA*

# Test GPIO
gpio readall
```

## Configuration

Edit `config.json` to customize settings:

```json
{
    "sensors": {
        "pms5003": {"enabled": true, "port": "/dev/ttyUSB0"},
        "mhz19": {"enabled": true, "port": "/dev/ttyUSB1"},
        "sgp30": {"enabled": true},
        "mq131": {"enabled": true, "channel": 0},
        "dht22": {"enabled": true, "pin": 4}
    },
    "alerts": {
        "pm2_5_threshold": 35,
        "co2_threshold": 1000,
        "ozone_threshold": 100
    }
}
```

## 🎮 Usage

### 🚀 Easy Start (Recommended)

```bash
# 1. Start the monitoring system
python start_airiq.py

# 2. In a separate terminal, start web dashboard
python ultra_simple_web_dashboard.py
```

### 📊 Access Your Dashboard

Open your web browser and go to:
- **Local**: http://localhost:5000
- **Network**: http://YOUR_PI_IP:5000 (from other devices)

### 🎯 Manual Control

```bash
# For Raspberry Pi with sensors
python AirIQ.py

# For testing/demo on any platform
python AirIQ_demo.py

# Web dashboard only
python ultra_simple_web_dashboard.py
```

### Access Web Dashboard

Open a web browser and navigate to:
- Local: `http://localhost:5000`
- Network: `http://[PI_IP_ADDRESS]:5000`

### Auto-start on Boot

Create systemd service:

```bash
sudo nano /etc/systemd/system/airiq.service
```

```ini
[Unit]
Description=Air Quality Monitor
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/air-quality-monitor
ExecStart=/home/pi/air-quality-monitor/venv/bin/python AirIQ.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable airiq.service
sudo systemctl start airiq.service
```

## Data Output

### CSV File Format
```csv
timestamp,pm1_0,pm2_5,pm10,co2,eco2,tvoc,ozone,temperature,humidity
2024-01-01 12:00:00,5.2,8.1,12.3,410,412,23,45,22.5,65.2
```

### Console Output
```
==================================================
Air Quality Monitor - 2024-01-01 12:00:00
==================================================
PM2.5: 8.1 μg/m³
CO2: 410 ppm
TVOC: 23 ppb
Ozone: 45 ppb
Temp: 22.5°C, Humidity: 65.2%
==================================================
```

## Air Quality Index (AQI) Ranges

| AQI Range | Category | PM2.5 (μg/m³) | Health Impact |
|-----------|----------|---------------|---------------|
| 0-50 | Good | 0-12 | Minimal impact |
| 51-100 | Moderate | 12.1-35.4 | Acceptable for most |
| 101-150 | Unhealthy for Sensitive | 35.5-55.4 | Sensitive groups affected |
| 151-200 | Unhealthy | 55.5-150.4 | Everyone affected |
| 201-300 | Very Unhealthy | 150.5-250.4 | Health alert |
| 301+ | Hazardous | 250.5+ | Emergency conditions |

## 🛠️ Troubleshooting

### 🔧 Common Issues

**❌ "Import errors" or "Module not found"**
```bash
# Solution: Use demo mode for testing
python AirIQ_demo.py
```

**❌ Web dashboard won't start**
```bash
# Install Flask if missing
pip install flask

# Or use demo version first
python AirIQ_demo.py
```

**❌ Platform detection issues**
```bash
# Force demo mode
python AirIQ_demo.py

# Force Raspberry Pi mode
python AirIQ.py
```

**❌ Sensor not detected (Raspberry Pi)**
```bash
# Check I2C devices
sudo i2cdetect -y 1

# Check UART devices
ls -la /dev/ttyUSB* /dev/ttyAMA*

# Fix permissions
sudo usermod -a -G dialout,gpio,i2c,spi $USER
```

**❌ Permission errors**
```bash
sudo chmod 666 /dev/ttyUSB*
sudo chmod 666 /dev/ttyAMA*
```

### Sensor Calibration

**CO2 Sensor (MH-Z19):**
- Requires 24-hour outdoor calibration
- Auto-calibration every 24 hours
- Manual calibration in fresh air: 400ppm

**Ozone Sensor (MQ131):**
- Requires burn-in period (24-48 hours)
- Calibrate in clean air (0 ppb)
- Temperature compensation needed

**PM Sensor (PMS5003):**
- Pre-calibrated from factory
- Clean regularly with compressed air
- Replace every 2-3 years

## API Endpoints

### REST API
- `GET /api/current` - Current readings
- `GET /api/chart/<parameter>?hours=24` - Chart data
- `GET /api/parameters` - Available parameters

### WebSocket Events
- `sensor_data` - Real-time sensor updates
- `connect/disconnect` - Connection status

## Safety Considerations

⚠️ **Important Safety Notes:**

1. **Power Requirements**: Use proper 5V 3A power supply
2. **Sensor Placement**: Avoid direct sunlight and moisture
3. **Ventilation**: Ensure adequate airflow around sensors
4. **Heat Management**: Monitor Pi temperature under load
5. **Regular Maintenance**: Clean sensors monthly
6. **Data Accuracy**: Allow 30-minute warm-up period

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 🎉 Current Status

✅ **Project Status**: Production Ready v1.0  
🧹 **Codebase**: Clean and streamlined (10 essential files)  
🎮 **Demo Mode**: Fully functional on any platform  
🌐 **Web Dashboard**: Responsive and real-time  
📊 **Data Logging**: CSV format with timestamps  
🚀 **Smart Launcher**: Auto-platform detection  

### 📊 What's Working Now
- ✅ Cross-platform demo with realistic sensor simulation
- ✅ Web dashboard at http://localhost:5000
- ✅ Real-time data logging to CSV
- ✅ Air Quality Index calculations
- ✅ Alert system for dangerous levels
- ✅ Mobile-responsive web interface

## 📄 License

This project is licensed under the MIT License - Open source and free to use!

## 🙏 Acknowledgments

- **Adafruit** for excellent sensor libraries
- **Raspberry Pi Foundation** for the amazing platform
- **Open source community** for inspiration and support

## 💬 Support

For issues, questions, or contributions:
- 📧 Create an issue on GitHub
- 🌟 Star the project if you find it useful
- 🤝 Pull requests welcome!

For issues and questions:
1. Check troubleshooting section
2. Search existing issues
3. Create new issue with:
   - Hardware configuration
   - Error messages
   - Log files

---

**Made with ❤️ for cleaner air monitoring**#   A i r - q u a l i t y - m o n i t o r  
 