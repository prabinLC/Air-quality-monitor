#!/usr/bin/env python3
"""
AIR QUALITY MONITOR DEMO VERSION
This version simulates sensor readings for demonstration on Windows
"""

import time
import json
import csv
import random
from datetime import datetime
from pathlib import Path
import logging

# Configure logging (Windows-compatible)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('airiq.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DemoSensor:
    """Demo sensor that generates realistic fake data"""
    def __init__(self, name, base_value, variation, unit):
        self.name = name
        self.base_value = base_value
        self.variation = variation
        self.unit = unit
        self.last_reading = None
        self.last_update = None
    
    def read(self):
        """Generate realistic sensor reading"""
        # Add some random variation
        value = self.base_value + random.uniform(-self.variation, self.variation)
        value = max(0, value)  # Ensure non-negative
        
        self.last_reading = {
            'value': round(value, 1),
            'unit': self.unit
        }
        self.last_update = datetime.now()
        return self.last_reading
    
    def is_healthy(self):
        return True


class AirQualityMonitorDemo:
    """Demo version of Air Quality Monitor"""
    
    def __init__(self):
        self.sensors = {
            'pm2_5': DemoSensor('PM2.5', 15, 10, 'μg/m³'),
            'pm10': DemoSensor('PM10', 25, 15, 'μg/m³'),
            'co2': DemoSensor('CO2', 450, 100, 'ppm'),
            'tvoc': DemoSensor('TVOC', 50, 30, 'ppb'),
            'ozone': DemoSensor('Ozone', 30, 20, 'ppb'),
            'temperature': DemoSensor('Temperature', 22, 5, '°C'),
            'humidity': DemoSensor('Humidity', 45, 15, '%')
        }
        
        self.data_file = 'air_quality_data.csv'
        self.config = {
            'alerts': {
                'pm2_5_threshold': 35,
                'co2_threshold': 1000,
                'ozone_threshold': 100
            },
            'logging': {'interval': 10}  # Faster for demo
        }
        
        self._init_csv_file()
        self.running = False
        
        logger.info("AIR QUALITY MONITOR DEMO INITIALIZED")
        logger.info("This demo simulates sensor readings for Windows testing")
    
    def _init_csv_file(self):
        """Initialize CSV file with headers"""
        if not Path(self.data_file).exists():
            headers = ['timestamp', 'pm2_5', 'pm10', 'co2', 'tvoc', 'ozone', 'temperature', 'humidity']
            with open(self.data_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
    
    def read_all_sensors(self):
        """Read all sensor data"""
        data = {'timestamp': datetime.now().isoformat()}
        
        for sensor_name, sensor in self.sensors.items():
            reading = sensor.read()
            data[sensor_name] = reading['value']
        
        return data
    
    def calculate_aqi(self, pm2_5_value):
        """Calculate Air Quality Index from PM2.5"""
        if pm2_5_value <= 12:
            aqi = int(pm2_5_value * 50 / 12)
            category = "Good"
            color = "🟢"
        elif pm2_5_value <= 35.4:
            aqi = int(50 + (pm2_5_value - 12) * 50 / 23.4)
            category = "Moderate"
            color = "🟡"
        elif pm2_5_value <= 55.4:
            aqi = int(100 + (pm2_5_value - 35.4) * 50 / 20)
            category = "Unhealthy for Sensitive"
            color = "🟠"
        elif pm2_5_value <= 150.4:
            aqi = int(150 + (pm2_5_value - 55.4) * 50 / 95)
            category = "Unhealthy"
            color = "🔴"
        elif pm2_5_value <= 250.4:
            aqi = int(200 + (pm2_5_value - 150.4) * 100 / 100)
            category = "Very Unhealthy"
            color = "🟣"
        else:
            aqi = int(300 + (pm2_5_value - 250.4) * 100 / 99.6)
            category = "Hazardous"
            color = "🟤"
        
        return {'aqi': aqi, 'category': category, 'color': color}
    
    def check_alerts(self, data):
        """Check for alert conditions"""
        alerts = []
        
        # PM2.5 alert
        if data['pm2_5'] > self.config['alerts']['pm2_5_threshold']:
            alerts.append(f"🚨 HIGH PM2.5: {data['pm2_5']} μg/m³")
        
        # CO2 alert
        if data['co2'] > self.config['alerts']['co2_threshold']:
            alerts.append(f"🚨 HIGH CO2: {data['co2']} ppm")
        
        # Ozone alert
        if data['ozone'] > self.config['alerts']['ozone_threshold']:
            alerts.append(f"🚨 HIGH OZONE: {data['ozone']} ppb")
        
        return alerts
    
    def log_data(self, data):
        """Log data to CSV file"""
        try:
            with open(self.data_file, 'a', newline='') as f:
                writer = csv.writer(f)
                row = [
                    data['timestamp'],
                    data['pm2_5'],
                    data['pm10'],
                    data['co2'],
                    data['tvoc'],
                    data['ozone'],
                    data['temperature'],
                    data['humidity']
                ]
                writer.writerow(row)
        except Exception as e:
            logger.error(f"Error logging data: {e}")
    
    def display_data(self, data, aqi_info, alerts):
        """Display data on console"""
        print("\n" + "=" * 60)
        print(f"🌬️  AIR QUALITY MONITOR - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # AQI Display
        print(f"\n{aqi_info['color']} AIR QUALITY INDEX: {aqi_info['aqi']} - {aqi_info['category']}")
        
        print("\n📊 CURRENT READINGS:")
        print(f"   PM2.5:        {data['pm2_5']:6.1f} μg/m³")
        print(f"   PM10:         {data['pm10']:6.1f} μg/m³")
        print(f"   CO₂:          {data['co2']:6.1f} ppm")
        print(f"   TVOC:         {data['tvoc']:6.1f} ppb")
        print(f"   Ozone:        {data['ozone']:6.1f} ppb")
        print(f"   Temperature:  {data['temperature']:6.1f} °C")
        print(f"   Humidity:     {data['humidity']:6.1f} %")
        
        # Alerts
        if alerts:
            print(f"\n⚠️  ALERTS:")
            for alert in alerts:
                print(f"   {alert}")
        else:
            print(f"\n✅ All readings within normal ranges")
        
        print("=" * 60)
        print("📝 Data logged to:", self.data_file)
        print("🌐 Web dashboard: Run 'python web_dashboard.py' then visit http://localhost:5000")
        print("⏹️  Press Ctrl+C to stop monitoring")
    
    def run_monitoring_loop(self):
        """Main monitoring loop"""
        self.running = True
        logger.info("Starting air quality monitoring demo...")
        
        print("\n" + "🌬️ " * 20)
        print("AIR QUALITY MONITOR DEMO")
        print("Simulating realistic sensor readings...")
        print("This would connect to real sensors on Raspberry Pi")
        print("🌬️ " * 20)
        
        try:
            cycle_count = 0
            while self.running:
                cycle_count += 1
                
                # Read all sensors
                data = self.read_all_sensors()
                
                # Calculate AQI
                aqi_info = self.calculate_aqi(data['pm2_5'])
                
                # Check alerts
                alerts = self.check_alerts(data)
                
                # Log data
                self.log_data(data)
                
                # Display data
                self.display_data(data, aqi_info, alerts)
                
                # Show progress
                print(f"\n📈 Reading #{cycle_count} - Next update in {self.config['logging']['interval']} seconds...")
                
                # Wait for next reading
                time.sleep(self.config['logging']['interval'])
                
        except KeyboardInterrupt:
            print("\n\n🛑 Monitoring stopped by user")
            logger.info("Demo monitoring stopped by user")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            logger.error(f"Demo monitoring error: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        self.running = False
        print("\n🧹 Cleanup completed")
        print("📊 Check your data in:", self.data_file)
        logger.info("Demo cleanup completed")


if __name__ == "__main__":
    print("🌬️  AIR QUALITY MONITOR - DEMO VERSION")
    print("=" * 50)
    print("This demo simulates sensor readings for Windows testing")
    print("On Raspberry Pi, this would connect to real sensors:")
    print("• PMS5003 (PM2.5/PM10)")
    print("• MH-Z19 (CO2)")
    print("• SGP30 (VOC)")
    print("• MQ131 (Ozone)")
    print("• DHT22 (Temperature/Humidity)")
    print("=" * 50)
    
    monitor = AirQualityMonitorDemo()
    monitor.run_monitoring_loop()