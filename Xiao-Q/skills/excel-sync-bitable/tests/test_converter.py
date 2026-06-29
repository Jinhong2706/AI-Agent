"""格式转换模块测试"""
import pytest
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from core.converter import infer_field_type, process_rich_text_cell, parse_exported_json


class TestInferFieldType:
    """字段类型推断测试"""
    
    def test_infer_integer(self):
        """测试整数类型"""
        series = pd.Series([1, 2, 3, 4, 5])
        assert infer_field_type(series) == 'number'
    
    def test_infer_float(self):
        """测试浮点类型"""
        series = pd.Series([1.1, 2.2, 3.3])
        assert infer_field_type(series) == 'number'
    
    def test_infer_text(self):
        """测试文本类型"""
        series = pd.Series(['hello', 'world', 'test'])
        assert infer_field_type(series) == 'text'
    
    def test_infer_datetime(self):
        """测试日期类型"""
        series = pd.Series(['2024-01-01', '2024-01-02', '2024-01-03'])
        assert infer_field_type(series) == 'datetime'
    
    def test_infer_empty(self):
        """测试空值列"""
        series = pd.Series([None, None, None])
        assert infer_field_type(series) == 'text'


class TestProcessRichTextCell:
    """富文本单元格处理测试"""
    
    def test_none_cell(self):
        """测试None值"""
        assert process_rich_text_cell(None) == ''
    
    def test_string_cell(self):
        """测试字符串值"""
        assert process_rich_text_cell('hello') == 'hello'
    
    def test_rich_text_cell(self):
        """测试富文本列表"""
        cell = [
            {'text': 'KR1：', 'type': 'text'},
            {'text': '填写关键结果1', 'type': 'text'}
        ]
        assert process_rich_text_cell(cell) == 'KR1：填写关键结果1'
    
    def test_number_cell(self):
        """测试数字值"""
        assert process_rich_text_cell(123) == '123'


class TestParseExportedJson:
    """JSON解析测试"""
    
    def test_parse_single_table(self):
        """测试单表解析"""
        data = {
            'tables': [{
                'meta': {'tableName': '测试表'},
                'rows': [
                    {'name': '张三', 'age': 25},
                    {'name': '李四', 'age': 30}
                ]
            }]
        }
        result = parse_exported_json(data)
        assert len(result) == 1
        assert result[0]['name'] == '测试表'
        assert len(result[0]['data']) == 2
    
    def test_parse_multiple_tables(self):
        """测试多表解析"""
        data = {
            'tables': [
                {'meta': {'tableName': '表1'}, 'rows': [{'a': 1}]},
                {'meta': {'tableName': '表2'}, 'rows': [{'b': 2}]}
            ]
        }
        result = parse_exported_json(data)
        assert len(result) == 2
    
    def test_parse_empty_rows(self):
        """测试空数据"""
        data = {
            'tables': [{
                'meta': {'tableName': '空表'},
                'rows': []
            }]
        }
        result = parse_exported_json(data)
        assert len(result) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
