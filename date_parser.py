# date_parser.py
from datetime import datetime

def parse_date(date_str, output_format='%d/%m/%Y'):
    date_formats = ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y']
    for fmt in date_formats:
        try:
            parsed_date = datetime.strptime(date_str, fmt)
            return parsed_date.strftime(output_format)
        except ValueError:
            continue
    return None

def extract_day_month(date_str):
    date_formats = ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y']
    for fmt in date_formats:
        try:
            parsed_date = datetime.strptime(date_str, fmt)
            return parsed_date.strftime('%d/%m')  # Chỉ trả về ngày và tháng
        except ValueError:
            continue
    return None