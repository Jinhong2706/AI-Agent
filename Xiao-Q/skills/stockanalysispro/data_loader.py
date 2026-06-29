import os
import struct
import pandas as pd
import numpy as np


class TdxDataLoader:
    TDX_DAY_RECORD_SIZE = 32

    def __init__(self, tdx_path=None):
        if tdx_path is None:
            tdx_path = self._find_tdx_path()
        self.tdx_path = tdx_path
        self.vipdoc_sh = os.path.join(tdx_path, 'vipdoc', 'sh', 'lday') if tdx_path else None
        self.vipdoc_sz = os.path.join(tdx_path, 'vipdoc', 'sz', 'lday') if tdx_path else None

    @staticmethod
    def _find_tdx_path():
        common_paths = [
            r'C:\new_tdx',
            r'C:\tdx',
            r'D:\new_tdx',
            r'D:\tdx',
            r'E:\new_tdx',
            r'E:\tdx',
            r'C:\Program Files\new_tdx',
            r'D:\Program Files\new_tdx',
        ]
        for p in common_paths:
            if os.path.isdir(p):
                vipdoc = os.path.join(p, 'vipdoc')
                if os.path.isdir(vipdoc):
                    return p
        return None

    def _parse_day_file(self, filepath):
        records = []
        with open(filepath, 'rb') as f:
            data = f.read()
        record_count = len(data) // self.TDX_DAY_RECORD_SIZE
        for i in range(record_count):
            offset = i * self.TDX_DAY_RECORD_SIZE
            record = data[offset:offset + self.TDX_DAY_RECORD_SIZE]
            date_int, open_p, high_p, low_p, close_p, amount, volume, reserved = struct.unpack(
                'IIIIIfII', record
            )
            records.append({
                'date': str(date_int),
                'open': open_p / 100.0,
                'high': high_p / 100.0,
                'low': low_p / 100.0,
                'close': close_p / 100.0,
                'amount': amount,
                'volume': volume,
            })
        return records

    @staticmethod
    def _format_date(date_str):
        if len(date_str) == 8:
            return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
        return date_str

    def load_stock(self, code):
        if code.startswith('6') or code.startswith('9'):
            prefix = 'sh'
            vipdoc = self.vipdoc_sh
        else:
            prefix = 'sz'
            vipdoc = self.vipdoc_sz

        if vipdoc is None or not os.path.isdir(vipdoc):
            return None

        filepath = os.path.join(vipdoc, f'{prefix}{code}.day')
        if not os.path.isfile(filepath):
            return None

        records = self._parse_day_file(filepath)
        if not records:
            return None

        for r in records:
            r['date'] = self._format_date(r['date'])

        return {
            'code': code,
            'name': code,
            'kline': records
        }

    def load_stock_with_name(self, code, name_map=None):
        data = self.load_stock(code)
        if data is None:
            return None
        if name_map and code in name_map:
            data['name'] = name_map[code]
        return data

    def scan_all(self, max_count=0):
        stock_list = []
        for vipdoc, prefix in [(self.vipdoc_sh, 'sh'), (self.vipdoc_sz, 'sz')]:
            if vipdoc is None or not os.path.isdir(vipdoc):
                continue
            for fname in os.listdir(vipdoc):
                if not fname.endswith('.day'):
                    continue
                code = fname.replace(prefix, '').replace('.day', '')
                if not code.isdigit():
                    continue
                if code.startswith('688') or code.startswith('8'):
                    continue
                stock_list.append(code)
                if max_count > 0 and len(stock_list) >= max_count:
                    return stock_list
        return stock_list

    def load_name_map(self):
        name_map = {}
        for base_dir in [self.vipdoc_sh, self.vipdoc_sz]:
            if base_dir is None:
                continue
            parent = os.path.dirname(base_dir)
            for fname in os.listdir(parent):
                if fname.endswith('.txt') and 'min' not in fname.lower():
                    fpath = os.path.join(parent, fname)
                    try:
                        with open(fpath, 'r', encoding='gbk', errors='ignore') as f:
                            for line in f:
                                parts = line.strip().split('|')
                                if len(parts) >= 2:
                                    name_map[parts[0]] = parts[1]
                    except Exception:
                        pass
        return name_map


class CSVDataLoader:
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir

    def load_stock(self, code):
        filepath = os.path.join(self.data_dir, f'{code}.csv')
        if not os.path.isfile(filepath):
            return None
        df = pd.read_csv(filepath)
        col_map = {}
        for col in df.columns:
            col_lower = col.strip().lower()
            if col_lower in ('date', '日期', 'trade_date'):
                col_map[col] = 'date'
            elif col_lower in ('open', '开盘', 'open_price'):
                col_map[col] = 'open'
            elif col_lower in ('high', '最高', 'high_price'):
                col_map[col] = 'high'
            elif col_lower in ('low', '最低', 'low_price'):
                col_map[col] = 'low'
            elif col_lower in ('close', '收盘', 'close_price'):
                col_map[col] = 'close'
            elif col_lower in ('volume', '成交量', 'vol'):
                col_map[col] = 'volume'
            elif col_lower in ('amount', '成交额', 'turnover'):
                col_map[col] = 'amount'
        df = df.rename(columns=col_map)
        records = df.to_dict(orient='records')
        for r in records:
            r['date'] = str(r.get('date', ''))
        return {
            'code': code,
            'name': code,
            'kline': records
        }

    def scan_all(self):
        stock_list = []
        if not os.path.isdir(self.data_dir):
            return stock_list
        for fname in os.listdir(self.data_dir):
            if fname.endswith('.csv'):
                code = fname.replace('.csv', '')
                stock_list.append(code)
        return stock_list


def generate_test_data(code='600519', name='贵州茅台', days=120, trend='bull'):
    np.random.seed(hash(code) % 2 ** 31)
    dates = pd.bdate_range(end=pd.Timestamp.today(), periods=days)
    base_price = 1800.0 if code == '600519' else 20.0

    if trend == 'bull':
        drift = 0.002
    elif trend == 'bear':
        drift = -0.001
    else:
        drift = 0.0

    returns = np.random.normal(drift, 0.02, days)
    prices = base_price * np.cumprod(1 + returns)

    kline = []
    for i, date in enumerate(dates):
        close = round(prices[i], 2)
        high = round(close * (1 + abs(np.random.normal(0, 0.01))), 2)
        low = round(close * (1 - abs(np.random.normal(0, 0.01))), 2)
        open_p = round(close * (1 + np.random.normal(0, 0.005)), 2)
        volume = int(np.random.uniform(50000, 200000))
        amount = round(close * volume * 100, 0)
        kline.append({
            'date': date.strftime('%Y-%m-%d'),
            'open': open_p,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume,
            'amount': amount
        })

    return {
        'code': code,
        'name': name,
        'kline': kline
    }
