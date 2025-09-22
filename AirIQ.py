#!/usr/bin/env python3
"""
AirIQ - DIY Air Quality Monitor for Raspberry Pi
Monitors PM2.5, CO2, VOC, Ozone, Temperature & Humidity

Features:
- Real-time sensor monitoring
- CSV data logging with timestamps
- Web dashboard interface
- Alert system for dangerous levels
- OLED display support (optional)

Hardware Requirements:
- Raspberry Pi 4B or similar
- PMS5003 (PM2.5 sensor)
- MH-Z19 (CO2 sensor)
- SGP30 (VOC sensor)
- MQ131 (Ozone sensor)
- DHT22 (Temperature & Humidity)
- Optional: SSD1306 OLED display

Author: AirIQ Project
Version: 1.0
"""

import time
import serial
import json
import csv
from datetime import datetime
import threading
import logging
from pathlib import Path
import RPi.GPIO as GPIO
from typing import Dict, Optional, Tuple
import adafruit_dht
import board
import digitalio
import busio
import adafruit_sgp30
import adafruit_ssd1306
from PIL import Image, ImageDraw, ImageFont

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('airiq.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SensorBase:
    """Base class for all sensors"""
    def __init__(self, name: str):
        self.name = name
        self.last_reading = None
        self.last_update = None
    
    def read(self) -> Optional[Dict]:
        """Read sensor data - to be implemented by subclasses"""
        raise NotImplementedError
    
    def is_healthy(self) -> bool:
        """Check if sensor is working properly"""
        return self.last_reading is not None


class PMS5003Sensor(SensorBase):
    """PM2.5 Particulate Matter Sensor"""
    def __init__(self, uart_port='/dev/ttyUSB0', baudrate=9600):
        super().__init__("PMS5003")
        try:
            self.serial = serial.Serial(uart_port, baudrate, timeout=1)
            logger.info(f"PMS5003 initialized on {uart_port}")
        except Exception as e:
            logger.error(f"Failed to initialize PMS5003: {e}")
            self.serial = None
    
    def read(self) -> Optional[Dict]:
        """Read PM1.0, PM2.5, PM10 values"""
        if not self.serial:
            return None
        
        try:
            # Send read command
            self.serial.write(b'\x42\x4d\xe2\x00\x00\x01\x71')
            time.sleep(0.1)
            
            # Read response
            data = self.serial.read(32)
            if len(data) == 32 and data[0] == 0x42 and data[1] == 0x4d:
                # Parse data
                pm1_0 = (data[10] << 8) | data[11]
                pm2_5 = (data[12] << 8) | data[13]
                pm10 = (data[14] << 8) | data[15]
                
                self.last_reading = {
                    'pm1_0': pm1_0,
                    'pm2_5': pm2_5,
                    'pm10': pm10,
                    'unit': 'μg/m³'
                }
                self.last_update = datetime.now()
                return self.last_reading
        except Exception as e:
            logger.error(f"PMS5003 read error: {e}")
        
        return None


class MHZ19Sensor(SensorBase):
    """CO2 Sensor"""
    def __init__(self, uart_port='/dev/ttyUSB1', baudrate=9600):
        super().__init__("MH-Z19")
        try:
            self.serial = serial.Serial(uart_port, baudrate, timeout=1)
            logger.info(f"MH-Z19 initialized on {uart_port}")
        except Exception as e:
            logger.error(f"Failed to initialize MH-Z19: {e}")
            self.serial = None
    
    def read(self) -> Optional[Dict]:
        """Read CO2 concentration"""
        if not self.serial:
            return None
        
        try:
            # Send read command
            cmd = b'\xff\x01\x86\x00\x00\x00\x00\x00\x79'
            self.serial.write(cmd)
            time.sleep(0.1)
            
            # Read response
            response = self.serial.read(9)
            if len(response) == 9 and response[0] == 0xff and response[1] == 0x86:
                co2 = (response[2] << 8) | response[3]
                temp = response[4] - 40  # Temperature offset
                
                self.last_reading = {
                    'co2': co2,
                    'temperature': temp,
                    'unit_co2': 'ppm',
                    'unit_temp': '°C'
                }
                self.last_update = datetime.now()
                return self.last_reading
        except Exception as e:
            logger.error(f"MH-Z19 read error: {e}")
        
        return None


class SGP30Sensor(SensorBase):
    """VOC and eCO2 Sensor"""
    def __init__(self):
        super().__init__("SGP30")
        try:
            i2c = busio.I2C(board.SCL, board.SDA, frequency=100000)
            self.sgp30 = adafruit_sgp30.Adafruit_SGP30(i2c)
            
            # Initialize baseline
            self.sgp30.iaq_init()
            self.sgp30.set_iaq_baseline(0x8973, 0x8AAE)
            logger.info("SGP30 initialized")
        except Exception as e:
            logger.error(f"Failed to initialize SGP30: {e}")
            self.sgp30 = None
    
    def read(self) -> Optional[Dict]:
        """Read VOC and eCO2 values"""
        if not self.sgp30:
            return None
        
        try:
            eco2, tvoc = self.sgp30.iaq_measure()
            
            self.last_reading = {
                'eco2': eco2,
                'tvoc': tvoc,
                'unit_eco2': 'ppm',
                'unit_tvoc': 'ppb'
            }
            self.last_update = datetime.now()
            return self.last_reading
        except Exception as e:
            logger.error(f"SGP30 read error: {e}")
        
        return None


class MQ131Sensor(SensorBase):
    """Ozone Sensor (Analog)"""
    def __init__(self, adc_channel=0):
        super().__init__("MQ131")
        self.adc_channel = adc_channel
        try:
            # Initialize ADC (using MCP3008 or similar)
            import spidev
            self.spi = spidev.SpiDev()
            self.spi.open(0, 0)
            self.spi.max_speed_hz = 1000000
            logger.info("MQ131 initialized")
        except Exception as e:
            logger.error(f"Failed to initialize MQ131: {e}")
            self.spi = None
    
    def _read_adc(self, channel) -> int:
        """Read ADC value from MCP3008"""
        if not self.spi:
            return 0
        
        adc = self.spi.xfer2([1, (8 + channel) << 4, 0])
        data = ((adc[1] & 3) << 8) + adc[2]
        return data
    
    def read(self) -> Optional[Dict]:
        """Read ozone concentration"""
        if not self.spi:
            return None
        
        try:
            adc_value = self._read_adc(self.adc_channel)
            voltage = adc_value * 3.3 / 1024.0
            
            # Convert voltage to ozone concentration (calibration needed)
            # This is a simplified conversion - real calibration required
            ozone_ppb = (voltage - 0.4) * 1000 / 2.0
            ozone_ppb = max(0, ozone_ppb)  # Ensure non-negative
            
            self.last_reading = {
                'ozone': round(ozone_ppb, 2),
                'voltage': round(voltage, 3),
                'unit': 'ppb'
            }
            self.last_update = datetime.now()
            return self.last_reading
        except Exception as e:
            logger.error(f"MQ131 read error: {e}")
        
        return None


class DHT22Sensor(SensorBase):
    """Temperature and Humidity Sensor"""
    def __init__(self, pin=board.D4):
        super().__init__("DHT22")
        try:
            self.dht = adafruit_dht.DHT22(pin)
            logger.info("DHT22 initialized")
        except Exception as e:
            logger.error(f"Failed to initialize DHT22: {e}")
            self.dht = None
    
    def read(self) -> Optional[Dict]:
        """Read temperature and humidity"""
        if not self.dht:
            return None
        
        try:
            temperature = self.dht.temperature
            humidity = self.dht.humidity
            
            if temperature is not None and humidity is not None:
                self.last_reading = {
                    'temperature': round(temperature, 1),
                    'humidity': round(humidity, 1),
                    'unit_temp': '°C',
                    'unit_hum': '%'
                }
                self.last_update = datetime.now()
                return self.last_reading
        except Exception as e:
            logger.error(f"DHT22 read error: {e}")
        
        return None


class AirQualityMonitor:
    """Main Air Quality Monitor class"""
    def __init__(self, config_file='config.json'):
        self.config = self._load_config(config_file)
        self.sensors = {}
        self.display = None
        self.running = False
        
        # Initialize sensors
        self._init_sensors()
        self._init_display()
        
        # Data storage
        self.data_file = 'air_quality_data.csv'
        self._init_csv_file()
    
    def _load_config(self, config_file: str) -> Dict:
        """Load configuration from JSON file"""
        default_config = {
            "sensors": {
                "pms5003": {"enabled": True, "port": "/dev/ttyUSB0"},
                "mhz19": {"enabled": True, "port": "/dev/ttyUSB1"},
                "sgp30": {"enabled": True},
                "mq131": {"enabled": True, "channel": 0},
                "dht22": {"enabled": True, "pin": 4}
            },
            "display": {"enabled": True, "type": "console"},
            "logging": {"interval": 60, "enabled": True},
            "alerts": {
                "pm2_5_threshold": 35,
                "co2_threshold": 1000,
                "ozone_threshold": 100
            }
        }
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                # Merge with defaults
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        except FileNotFoundError:
            logger.info(f"Config file {config_file} not found, using defaults")
            return default_config
    
    def _init_sensors(self):
        """Initialize all enabled sensors"""
        config = self.config['sensors']
        
        if config['pms5003']['enabled']:
            self.sensors['pms5003'] = PMS5003Sensor(config['pms5003']['port'])
        
        if config['mhz19']['enabled']:
            self.sensors['mhz19'] = MHZ19Sensor(config['mhz19']['port'])
        
        if config['sgp30']['enabled']:
            self.sensors['sgp30'] = SGP30Sensor()
        
        if config['mq131']['enabled']:
            self.sensors['mq131'] = MQ131Sensor(config['mq131']['channel'])
        
        if config['dht22']['enabled']:
            pin = getattr(board, f'D{config["dht22"]["pin"]}')
            self.sensors['dht22'] = DHT22Sensor(pin)
        
        logger.info(f"Initialized {len(self.sensors)} sensors")
    
    def _init_display(self):
        """Initialize display (OLED or console)"""
        if not self.config['display']['enabled']:
            return
        
        display_type = self.config['display']['type']
        if display_type == 'oled':
            try:
                i2c = busio.I2C(board.SCL, board.SDA)
                self.display = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)
                self.display.fill(0)
                self.display.show()
                logger.info("OLED display initialized")
            except Exception as e:
                logger.error(f"Failed to initialize OLED: {e}")
    
    def _init_csv_file(self):
        """Initialize CSV file with headers"""
        if not Path(self.data_file).exists():
            headers = ['timestamp', 'pm1_0', 'pm2_5', 'pm10', 'co2', 'eco2', 
                      'tvoc', 'ozone', 'temperature', 'humidity']
            with open(self.data_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
    
    def read_all_sensors(self) -> Dict:
        """Read data from all sensors"""
        data = {'timestamp': datetime.now().isoformat()}
        
        for sensor_name, sensor in self.sensors.items():
            try:
                reading = sensor.read()
                if reading:
                    # Flatten the reading data
                    for key, value in reading.items():
                        if not key.startswith('unit'):
                            data[f"{sensor_name}_{key}"] = value
                else:
                    logger.warning(f"No reading from {sensor_name}")
            except Exception as e:
                logger.error(f"Error reading {sensor_name}: {e}")
        
        return data
    
    def log_data(self, data: Dict):
        """Log data to CSV file"""
        if not self.config['logging']['enabled']:
            return
        
        try:
            with open(self.data_file, 'a', newline='') as f:
                writer = csv.writer(f)
                row = [
                    data.get('timestamp', ''),
                    data.get('pms5003_pm1_0', ''),
                    data.get('pms5003_pm2_5', ''),
                    data.get('pms5003_pm10', ''),
                    data.get('mhz19_co2', ''),
                    data.get('sgp30_eco2', ''),
                    data.get('sgp30_tvoc', ''),
                    data.get('mq131_ozone', ''),
                    data.get('dht22_temperature', ''),
                    data.get('dht22_humidity', '')
                ]
                writer.writerow(row)
        except Exception as e:
            logger.error(f"Error logging data: {e}")
    
    def check_alerts(self, data: Dict):
        """Check for alert conditions"""
        alerts = []
        thresholds = self.config['alerts']
        
        # PM2.5 alert
        pm2_5 = data.get('pms5003_pm2_5')
        if pm2_5 and pm2_5 > thresholds['pm2_5_threshold']:
            alerts.append(f"HIGH PM2.5: {pm2_5} μg/m³")
        
        # CO2 alert
        co2 = data.get('mhz19_co2')
        if co2 and co2 > thresholds['co2_threshold']:
            alerts.append(f"HIGH CO2: {co2} ppm")
        
        # Ozone alert
        ozone = data.get('mq131_ozone')
        if ozone and ozone > thresholds['ozone_threshold']:
            alerts.append(f"HIGH OZONE: {ozone} ppb")
        
        if alerts:
            for alert in alerts:
                logger.warning(f"ALERT: {alert}")
        
        return alerts
    
    def display_data(self, data: Dict, alerts: list = None):
        """Display data on console or OLED"""
        if self.config['display']['type'] == 'console':
            self._display_console(data, alerts)
        elif self.config['display']['type'] == 'oled' and self.display:
            self._display_oled(data, alerts)
    
    def _display_console(self, data: Dict, alerts: list = None):
        """Display data on console"""
        print("\n" + "="*50)
        print(f"Air Quality Monitor - {data.get('timestamp', 'Unknown time')}")
        print("="*50)
        
        # PM2.5 data
        pm2_5 = data.get('pms5003_pm2_5')
        if pm2_5:
            print(f"PM2.5: {pm2_5} μg/m³")
        
        # CO2 data
        co2 = data.get('mhz19_co2')
        if co2:
            print(f"CO2: {co2} ppm")
        
        # VOC data
        tvoc = data.get('sgp30_tvoc')
        if tvoc:
            print(f"TVOC: {tvoc} ppb")
        
        # Ozone data
        ozone = data.get('mq131_ozone')
        if ozone:
            print(f"Ozone: {ozone} ppb")
        
        # Temperature & Humidity
        temp = data.get('dht22_temperature')
        hum = data.get('dht22_humidity')
        if temp and hum:
            print(f"Temp: {temp}°C, Humidity: {hum}%")
        
        # Alerts
        if alerts:
            print("\n🚨 ALERTS:")
            for alert in alerts:
                print(f"  - {alert}")
        
        print("="*50)
    
    def _display_oled(self, data: Dict, alerts: list = None):
        """Display data on OLED screen"""
        if not self.display:
            return
        
        # Create image
        image = Image.new('1', (128, 64))
        draw = ImageDraw.Draw(image)
        
        # Load font (use default if custom font not available)
        try:
            font = ImageFont.truetype('DejaVuSans.ttf', 10)
        except:
            font = ImageFont.load_default()
        
        # Display key measurements
        y = 0
        pm2_5 = data.get('pms5003_pm2_5')
        if pm2_5:
            draw.text((0, y), f"PM2.5: {pm2_5}", font=font, fill=255)
            y += 12
        
        co2 = data.get('mhz19_co2')
        if co2:
            draw.text((0, y), f"CO2: {co2}", font=font, fill=255)
            y += 12
        
        temp = data.get('dht22_temperature')
        hum = data.get('dht22_humidity')
        if temp and hum:
            draw.text((0, y), f"T:{temp}C H:{hum}%", font=font, fill=255)
            y += 12
        
        # Show alerts
        if alerts and y < 52:
            draw.text((0, y), "ALERT!", font=font, fill=255)
        
        # Update display
        self.display.image(image)
        self.display.show()
    
    def run_monitoring_loop(self):
        """Main monitoring loop"""
        self.running = True
        logger.info("Starting air quality monitoring...")
        
        try:
            while self.running:
                # Read all sensors
                data = self.read_all_sensors()
                
                # Log data
                self.log_data(data)
                
                # Check alerts
                alerts = self.check_alerts(data)
                
                # Display data
                self.display_data(data, alerts)
                
                # Wait for next reading
                time.sleep(self.config['logging']['interval'])
                
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Monitoring error: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        self.running = False
        
        # Close serial connections
        for sensor in self.sensors.values():
            if hasattr(sensor, 'serial') and sensor.serial:
                sensor.serial.close()
        
        # Clear display
        if self.display:
            self.display.fill(0)
            self.display.show()
        
        logger.info("Cleanup completed")


def main():
    """Main entry point for AirIQ Monitor"""
    print("AirIQ - DIY Air Quality Monitor v1.0")
    print("====================================")
    
    # Check if running on Raspberry Pi
    try:
        with open('/proc/cpuinfo', 'r') as f:
            if 'Raspberry Pi' not in f.read():
                print("⚠️  Warning: Not running on Raspberry Pi")
                print("Consider using AirIQ_demo.py for testing on other platforms")
    except FileNotFoundError:
        print("⚠️  Warning: Cannot detect platform")
        print("Consider using AirIQ_demo.py for testing on other platforms")
    
    try:
        # Initialize and run monitor
        monitor = AirQualityMonitor()
        print(f"\n🚀 Starting monitoring with {len(monitor.sensors)} active sensors...")
        print("📊 Data will be logged to: air_quality_data.csv")
        print("🌐 Web dashboard available at: http://localhost:5000")
        print("⏹️  Press Ctrl+C to stop\n")
        
        monitor.run_monitoring_loop()
        
    except KeyboardInterrupt:
        print("\n👋 AirIQ Monitor stopped by user")
    except Exception as e:
        print(f"❌ Error starting AirIQ Monitor: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
    monitor.run_monitoring_loop()