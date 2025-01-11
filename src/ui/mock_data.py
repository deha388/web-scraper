import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_mock_prices(start_date=None, end_date=None):
    if start_date is None:
        start_date = datetime.now()
    if end_date is None:
        end_date = start_date + timedelta(days=7)
    
    # Haftalık tarih aralığı oluştur
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    competitors = {
        'Rudder&Moor': {'base_price': 1000, 'volatility': 100},
        'SailTime': {'base_price': 1200, 'volatility': 150},
        'NaviGo': {'base_price': 900, 'volatility': 80}
    }
    
    data = []
    for date in dates:
        for comp, price_info in competitors.items():
            # Hafta içi/sonu fiyat farkı simülasyonu
            weekend_multiplier = 1.2 if date.weekday() >= 5 else 1.0
            base_price = price_info['base_price'] * weekend_multiplier
            
            price = base_price + np.random.randint(
                -price_info['volatility'],
                price_info['volatility']
            )
            
            data.append({
                'date': date,
                'competitor': comp,
                'price': price,
                'our_price': 1100 * weekend_multiplier + np.random.randint(-100, 100)
            })
    
    return pd.DataFrame(data)

def get_mock_boats():
    return [
        {"id": 1, "name": "Yacht A", "type": "Sailing Yacht", "length": "42ft"},
        {"id": 2, "name": "Catamaran B", "type": "Catamaran", "length": "38ft"},
        {"id": 3, "name": "Motor Yacht C", "type": "Motor Yacht", "length": "45ft"}
    ] 