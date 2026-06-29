"""URL解析和Token提取模块"""
import re
import json
import subprocess
from typing import Dict, Optional, Tuple


def extract_token_from_url(url: str) -> Dict[str, Optional[str]]:
    """从URL中提取token信息，支持多维表格和电子表格
    
    Args:
        url: 飞书表格URL，支持格式：
            - https://xxx.feishu.cn/base/TOKEN
            - https://xxx.feishu.cn/sheets/TOKEN
            - https://xxx.feishu.cn/wiki/TOKEN
    
    Returns:
        dict: {
            'type': 'bitable' | 'sheet' | None,
            'token': str | None,
            'table_id': str | None,
            'sheet_id': str | None
        }
    """
    token_info = {
        'type': None,
        'token': None,
        'table_id': None,
        'sheet_id': None
    }
    
    # 尝试匹配 /base/TOKEN
    base_match = re.search(r'/base/([a-zA-Z0-9]+)', url)
    if base_match:
        token_info['type'] = 'bitable'
        token_info['token'] = base_match.group(1)
    
    # 尝试匹配 /sheets/TOKEN
    sheet_match = re.search(r'/sheets/([a-zA-Z0-9]+)', url)
    if sheet_match:
        token_info['type'] = 'sheet'
        token_info['token'] = sheet_match.group(1)
    
    # 尝试匹配 /wiki/TOKEN
    wiki_match = re.search(r'/wiki/([a-zA-Z0-9]+)', url)
    if wiki_match:
        wiki_token = wiki_match.group(1)
        cmd = ['lark-cli', 'wiki', 'spaces', 'get_node', '--params', json.dumps({"token": wiki_token})]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                if data.get('code') == 0:
                    node = data.get('data', {}).get('node', {})
                    obj_type = node.get('obj_type')
                    token_info['token'] = node.get('obj_token')
                    if obj_type == 'bitable':
                        token_info['type'] = 'bitable'
                    elif obj_type == 'sheet':
                        token_info['type'] = 'sheet'
            except:
                pass
    
    # 尝试匹配 table=TABLE_ID 或 sheet=SHEET_ID
    table_match = re.search(r'table=([a-zA-Z0-9]+)', url)
    if table_match:
        token_info['table_id'] = table_match.group(1)
    
    sheet_id_match = re.search(r'sheet=([a-zA-Z0-9]+)', url)
    if sheet_id_match:
        token_info['sheet_id'] = sheet_id_match.group(1)
    
    return token_info


def extract_base_token_from_url(url: str) -> Tuple[Optional[str], Optional[str]]:
    """从URL中提取base_token和table_id（兼容旧版）
    
    Args:
        url: 多维表格URL
    
    Returns:
        tuple: (base_token, table_id)
    """
    token_info = extract_token_from_url(url)
    if token_info['type'] == 'bitable':
        return token_info['token'], token_info['table_id']
    return None, None


def col_to_letter(n: int) -> str:
    """将列号转换为Excel列字母
    
    Args:
        n: 列号（1-based）
    
    Returns:
        str: 列字母（如 A, B, ..., Z, AA, AB, ...）
    
    Examples:
        >>> col_to_letter(1)
        'A'
        >>> col_to_letter(26)
        'Z'
        >>> col_to_letter(27)
        'AA'
    """
    result = ''
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        result = chr(65 + remainder) + result
    return result
