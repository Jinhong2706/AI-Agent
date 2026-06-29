"""导入模块测试 - 新版 lark-cli 命令"""
import pytest
import pandas as pd
import sys
import os
import tempfile
import json
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from core.importer import (
    convert_excel_to_json,
    create_new_bitable,
    sync_to_existing_bitable,
    import_from_excel
)


class TestConvertExcelToJson:
    """Excel 转 JSON 测试"""
    
    def test_convert_simple_excel(self, tmp_path):
        """测试简单 Excel 转换"""
        # 创建测试 Excel
        df = pd.DataFrame({
            '姓名': ['张三', '李四'],
            '年龄': [25, 30],
            '日期': ['2024-01-01', '2024-01-02']
        })
        excel_path = str(tmp_path / "test.xlsx")
        df.to_excel(excel_path, index=False)
        
        # 执行转换
        records, field_types = convert_excel_to_json(excel_path)
        
        # 验证
        assert len(records) == 2
        assert '姓名' in field_types
        assert '年龄' in field_types
        assert field_types['姓名'] == 'text'
        assert field_types['年龄'] == 'number'
    
    def test_convert_with_datetime(self, tmp_path):
        """测试日期字段转换"""
        df = pd.DataFrame({
            '事件': ['事件A', '事件B'],
            '时间': pd.to_datetime(['2024-01-01 10:00', '2024-01-02 11:00'])
        })
        excel_path = str(tmp_path / "test_datetime.xlsx")
        df.to_excel(excel_path, index=False)
        
        records, field_types = convert_excel_to_json(excel_path)
        
        assert len(records) == 2
        assert field_types['时间'] == 'datetime'
        # 验证日期格式
        assert '2024-01-01' in records[0]['时间']
    
    def test_convert_nonexistent_file(self):
        """测试文件不存在"""
        with pytest.raises(FileNotFoundError):
            convert_excel_to_json("/nonexistent/path.xlsx")
    
    def test_convert_with_nulls(self, tmp_path):
        """测试空值处理"""
        df = pd.DataFrame({
            '姓名': ['张三', None, '王五'],
            '分数': [90, pd.NA, 85]
        })
        excel_path = str(tmp_path / "test_nulls.xlsx")
        df.to_excel(excel_path, index=False)
        
        records, field_types = convert_excel_to_json(excel_path)
        
        assert len(records) == 3
        assert records[1]['姓名'] is None


class TestCreateNewBitable:
    """创建新多维表格测试"""
    
    @patch('subprocess.run')
    def test_create_basic_flow(self, mock_run, tmp_path):
        """测试基本创建流程"""
        # 准备测试数据
        df = pd.DataFrame({
            '姓名': ['张三', '李四'],
            '年龄': [25, 30]
        })
        excel_path = str(tmp_path / "test.xlsx")
        df.to_excel(excel_path, index=False)
        
        # Mock subprocess 响应
        mock_run.side_effect = [
            # Base 创建响应
            MagicMock(returncode=0, stdout='{"token": "app_test123"}'),
            # Table 创建响应
            MagicMock(returncode=0, stdout='{"table_id": "tbl_test456"}'),
            # 字段创建响应
            MagicMock(returncode=0, stdout='{}'),
            MagicMock(returncode=0, stdout='{}'),
            # 记录插入响应
            MagicMock(returncode=0, stdout='{"created": true}'),
            MagicMock(returncode=0, stdout='{"created": true}')
        ]
        
        # 执行
        result = create_new_bitable(excel_path, "测试应用", "测试表")
        
        # 验证
        assert result['base_token'] == 'app_test123'
        assert result['table_id'] == 'tbl_test456'
        assert result['records_count'] == 2
    
    @patch('subprocess.run')
    def test_create_base_failure(self, mock_run, tmp_path):
        """测试 Base 创建失败"""
        df = pd.DataFrame({'姓名': ['张三']})
        excel_path = str(tmp_path / "test.xlsx")
        df.to_excel(excel_path, index=False)
        
        mock_run.return_value = MagicMock(returncode=1, stderr='创建失败')
        
        with pytest.raises(SystemExit):
            create_new_bitable(excel_path, "测试应用", "测试表")


class TestSyncToExistingBitable:
    """同步到现有多维表格测试"""
    
    @patch('subprocess.run')
    def test_sync_with_full_url(self, mock_run, tmp_path):
        """测试使用完整 URL 同步"""
        df = pd.DataFrame({
            '姓名': ['张三'],
            '年龄': [25]
        })
        excel_path = str(tmp_path / "test.xlsx")
        df.to_excel(excel_path, index=False)
        
        # Mock 响应
        mock_run.side_effect = [
            # 记录同步响应
            MagicMock(returncode=0, stdout='{"created": true}')
        ]
        
        url = "https://example.feishu.cn/base/TGA4boMuxanzjfsrqpKcrrHgnhb?table=tblX1nRl2H8F051h"
        result = sync_to_existing_bitable(excel_path, url)
        
        assert result['records_count'] == 1
        assert 'base_token' in result
    
    @patch('subprocess.run')
    def test_sync_with_table_name(self, mock_run, tmp_path):
        """测试使用表名查找"""
        df = pd.DataFrame({'姓名': ['张三']})
        excel_path = str(tmp_path / "test.xlsx")
        df.to_excel(excel_path, index=False)
        
        # Mock 响应
        mock_run.side_effect = [
            # Table list 响应
            MagicMock(returncode=0, stdout='[{"name": "测试表", "table_id": "tbl_test"}]'),
            # 记录同步响应
            MagicMock(returncode=0, stdout='{"created": true}')
        ]
        
        url = "https://example.feishu.cn/base/app_test"
        result = sync_to_existing_bitable(excel_path, url, table_name="测试表")
        
        assert result['records_count'] == 1


class TestImportFromExcel:
    """统一导入入口测试"""
    
    @patch('core.importer.sync_to_existing_bitable')
    def test_import_with_url(self, mock_sync, tmp_path):
        """测试带 URL 的导入"""
        df = pd.DataFrame({'姓名': ['张三']})
        excel_path = str(tmp_path / "test.xlsx")
        df.to_excel(excel_path, index=False)
        
        mock_sync.return_value = {'records_count': 1}
        
        result = import_from_excel(
            excel_path,
            target_url="https://example.feishu.cn/base/app_test"
        )
        
        assert result['records_count'] == 1
        mock_sync.assert_called_once()
    
    @patch('core.importer.create_new_bitable')
    def test_import_without_url(self, mock_create, tmp_path):
        """测试不带 URL 的导入（创建新表）"""
        df = pd.DataFrame({'姓名': ['张三']})
        excel_path = str(tmp_path / "test.xlsx")
        df.to_excel(excel_path, index=False)
        
        mock_create.return_value = {'records_count': 1}
        
        result = import_from_excel(excel_path, app_name="测试应用")
        
        assert result['records_count'] == 1
        mock_create.assert_called_once()
    
    @patch('core.importer.create_new_bitable')
    def test_import_uses_filename_as_app_name(self, mock_create, tmp_path):
        """测试使用文件名作为应用名"""
        df = pd.DataFrame({'姓名': ['张三']})
        excel_path = str(tmp_path / "我的数据.xlsx")
        df.to_excel(excel_path, index=False)
        
        mock_create.return_value = {'records_count': 1}
        
        result = import_from_excel(excel_path)
        
        # 验证使用了文件名
        call_args = mock_create.call_args
        assert '我的数据' in call_args[0]
