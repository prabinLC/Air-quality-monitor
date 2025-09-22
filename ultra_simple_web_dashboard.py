#!/usr/bin/env python3
"""
Ultra-Simple Web Dashboard for Air Quality Monitor
No external dependencies except Flask
"""

from flask import Flask, render_template, jsonify, request
import json
import csv
from datetime import datetime, timedelta
from pathlib import Path

app = Flask(__name__)

class UltraSimpleWebDashboard:
    def __init__(self, data_file='air_quality_data.csv'):
        self.data_file = data_file
    
    def get_current_readings(self):
        """Get the most recent sensor readings from CSV"""
        try:
            if not Path(self.data_file).exists():
                # Return demo data if no CSV exists
                return {
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'pm2_5': 15.2,
                    'pm10': 22.1,
                    'co2': 410,
                    'tvoc': 45,
                    'ozone': 25,
                    'temperature': 22.5,
                    'humidity': 55.0
                }
            
            # Read the last line of CSV file
            with open(self.data_file, 'r') as f:
                lines = f.readlines()
                if len(lines) < 2:  # Header + at least one data row
                    return {}
                
                # Get header and last data row
                header = lines[0].strip().split(',')
                last_row = lines[-1].strip().split(',')
                
                # Create dictionary from header and data
                readings = {}
                for i, col in enumerate(header):
                    if i < len(last_row):
                        if col == 'timestamp':
                            # Parse and reformat timestamp
                            try:
                                dt = datetime.fromisoformat(last_row[i].replace('Z', '+00:00'))
                                readings[col] = dt.strftime('%Y-%m-%d %H:%M:%S')
                            except:
                                readings[col] = last_row[i]
                        else:
                            try:
                                readings[col] = float(last_row[i])
                            except:
                                readings[col] = last_row[i]
                
                return readings
                
        except Exception as e:
            print(f"Error reading CSV: {e}")
            return {}
    
    def get_recent_data(self, hours=24):
        """Get recent data points for simple charting"""
        try:
            if not Path(self.data_file).exists():
                return []
            
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_data = []
            
            with open(self.data_file, 'r') as f:
                lines = f.readlines()
                if len(lines) < 2:
                    return []
                
                header = lines[0].strip().split(',')
                
                for line in lines[1:]:  # Skip header
                    row = line.strip().split(',')
                    if len(row) >= len(header):
                        try:
                            # Parse timestamp
                            timestamp_str = row[0]
                            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                            
                            if dt >= cutoff_time:
                                data_point = {'timestamp': timestamp_str}
                                for i, col in enumerate(header[1:], 1):  # Skip timestamp column
                                    if i < len(row):
                                        try:
                                            data_point[col] = float(row[i])
                                        except:
                                            data_point[col] = 0
                                recent_data.append(data_point)
                        except:
                            continue
                            
            return recent_data[-50:]  # Return last 50 points max
            
        except Exception as e:
            print(f"Error getting recent data: {e}")
            return []
    
    def get_air_quality_index(self, pm2_5_value):
        """Calculate AQI based on PM2.5"""
        if pm2_5_value is None or pm2_5_value == 0:
            return {'aqi': 0, 'category': 'Unknown', 'color': '#gray'}
        
        if pm2_5_value <= 12:
            return {'aqi': int(pm2_5_value * 50 / 12), 'category': 'Good', 'color': '#00e400'}
        elif pm2_5_value <= 35.4:
            return {'aqi': int(50 + (pm2_5_value - 12) * 50 / 23.4), 'category': 'Moderate', 'color': '#ffff00'}
        elif pm2_5_value <= 55.4:
            return {'aqi': int(100 + (pm2_5_value - 35.4) * 50 / 20), 'category': 'Unhealthy for Sensitive', 'color': '#ff7e00'}
        elif pm2_5_value <= 150.4:
            return {'aqi': int(150 + (pm2_5_value - 55.4) * 50 / 95), 'category': 'Unhealthy', 'color': '#ff0000'}
        elif pm2_5_value <= 250.4:
            return {'aqi': int(200 + (pm2_5_value - 150.4) * 100 / 100), 'category': 'Very Unhealthy', 'color': '#8f3f97'}
        else:
            return {'aqi': int(300 + (pm2_5_value - 250.4) * 100 / 99.6), 'category': 'Hazardous', 'color': '#7e0023'}

# Create dashboard instance
dashboard = UltraSimpleWebDashboard()

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('ultra_simple_dashboard.html')

@app.route('/api/current')
def api_current():
    """API endpoint for current readings"""
    readings = dashboard.get_current_readings()
    
    # Calculate AQI if PM2.5 is available
    pm2_5_value = readings.get('pm2_5', 0)
    aqi_info = dashboard.get_air_quality_index(pm2_5_value)
    
    return jsonify({
        'readings': readings,
        'aqi': aqi_info,
        'status': 'ok'
    })

@app.route('/api/recent/<parameter>')
def api_recent(parameter):
    """API endpoint for recent data points"""
    hours = request.args.get('hours', 6, type=int)
    recent_data = dashboard.get_recent_data(hours)
    
    # Extract specific parameter
    timestamps = []
    values = []
    
    for data_point in recent_data:
        if parameter in data_point:
            timestamps.append(data_point['timestamp'])
            values.append(data_point[parameter])
    
    return jsonify({
        'parameter': parameter,
        'timestamps': timestamps,
        'values': values,
        'count': len(values)
    })

@app.route('/api/stats')
def api_stats():
    """API endpoint for basic statistics"""
    recent_data = dashboard.get_recent_data(24)  # Last 24 hours
    
    stats = {
        'total_readings': len(recent_data),
        'data_available': len(recent_data) > 0,
        'oldest_reading': recent_data[0]['timestamp'] if recent_data else None,
        'newest_reading': recent_data[-1]['timestamp'] if recent_data else None,
    }
    
    return jsonify(stats)

if __name__ == '__main__':
    print("🌐 Starting Ultra-Simple Air Quality Monitor Web Dashboard...")
    print("📊 Access the dashboard at: http://localhost:5000")
    print("🔄 This version reads directly from CSV file")
    print("⏹️  Press Ctrl+C to stop")
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n🛑 Web dashboard stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Make sure port 5000 is available")