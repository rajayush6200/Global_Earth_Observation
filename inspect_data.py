import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')

files = {
    'avg_dataset.csv': 'Dataset/avg_dataset.csv',
    'Global_sea_level_rise.csv': 'Dataset/Global_sea_level_rise.csv',
    'GlobalTemperatures.csv': 'Dataset/GlobalTemperatures.csv',
    'historical_emissions.csv': 'Dataset/historical_emissions.csv',
}
for name, path in files.items():
    df = pd.read_csv(path)
    print(f'=== {name} ===')
    print(f'  Shape: {df.shape}')
    print(f'  Cols: {list(df.columns)}')
    print(df.head(3).to_string())
    print()
