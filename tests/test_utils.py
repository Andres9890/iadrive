import unittest
import os
import tempfile
import time
from datetime import datetime

from iadrive.utils import (
    key_value_to_dict, 
    sanitize_identifier, 
    get_oldest_file_date, 
    extract_file_types,
    get_collaborators
)


class UtilsTest(unittest.TestCase):

    def test_key_value_to_dict_single_item(self):
        """Test converting single key:value to dict"""
        result = key_value_to_dict(['key:value'])
        expected = {'key': 'value'}
        self.assertEqual(result, expected)

    def test_key_value_to_dict_multiple_items(self):
        """Test converting multiple key:value pairs to dict"""
        result = key_value_to_dict(['key1:value1', 'key2:value2'])
        expected = {'key1': 'value1', 'key2': 'value2'}
        self.assertEqual(result, expected)

    def test_key_value_to_dict_multiple_values_same_key(self):
        """Test multiple values for same key"""
        result = key_value_to_dict(['key:value1', 'key:value2'])
        expected = {'key': ['value1', 'value2']}
        self.assertEqual(result, expected)

    def test_key_value_to_dict_empty_list(self):
        """Test empty input"""
        result = key_value_to_dict([])
        expected = {}
        self.assertEqual(result, expected)

    def test_key_value_to_dict_none_input(self):
        """Test None input"""
        result = key_value_to_dict(None)
        expected = {}
        self.assertEqual(result, expected)

    def test_sanitize_identifier_valid(self):
        """Test preserving valid identifiers"""
        valid = [
            'drive-1-0axLqCuOUNbBIe3Cz6Y1KojGg4iXg1h',
            'drive-test123',
            'drive-abc_def-ghi'
        ]
        clean = [sanitize_identifier(x) for x in valid]
        self.assertEqual(valid, clean)

    def test_sanitize_identifier_invalid_chars(self):
        """Test sanitizing invalid characters"""
        bad = [
            'drive:test:123',
            'drive@test#123',
            'drive test 123'
        ]
        expected = [
            'drive-test-123',
            'drive-test-123',
            'drive-test-123'
        ]
        clean = [sanitize_identifier(x) for x in bad]
        self.assertEqual(expected, clean)

    def test_sanitize_identifier_case_preservation(self):
        """Test preserving original case"""
        result = sanitize_identifier('DRIVE-Test123')
        expected = 'DRIVE-Test123'  # Should preserve original case
        self.assertEqual(result, expected)

    def test_sanitize_identifier_consecutive_hyphens(self):
        """Test removing consecutive hyphens"""
        result = sanitize_identifier('drive---test---123')
        expected = 'drive-test-123'
        self.assertEqual(result, expected)

    def test_sanitize_identifier_leading_trailing_hyphens(self):
        """Test removing leading/trailing hyphens"""
        result = sanitize_identifier('-drive-test-123-')
        expected = 'drive-test-123'
        self.assertEqual(result, expected)

    def test_get_oldest_file_date(self):
        """Test getting oldest file date"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create files with different timestamps
            file1 = os.path.join(temp_dir, 'file1.txt')
            file2 = os.path.join(temp_dir, 'file2.txt')
            
            with open(file1, 'w') as f:
                f.write('content1')
            with open(file2, 'w') as f:
                f.write('content2')
            
            # Modify file1 to be older
            old_time = time.time() - 86400  # 1 day ago
            os.utime(file1, (old_time, old_time))
            
            files = [file1, file2]
            date_str, year_str = get_oldest_file_date(files)
            
            expected_date = datetime.fromtimestamp(old_time).strftime('%Y-%m-%d')
            expected_year = datetime.fromtimestamp(old_time).strftime('%Y')
            
            self.assertEqual(date_str, expected_date)
            self.assertEqual(year_str, expected_year)

    def test_get_oldest_file_date_no_files(self):
        """Test getting oldest file date with empty list"""
        files = []
        date_str, year_str = get_oldest_file_date(files)
        
        # Should return current date as fallback
        current_date = datetime.now().strftime('%Y-%m-%d')
        current_year = datetime.now().strftime('%Y')
        
        self.assertEqual(date_str, current_date)
        self.assertEqual(year_str, current_year)

    def test_extract_file_types(self):
        """Test extracting file types from file list"""
        files = [
            '/path/to/file.txt',
            '/path/to/file.PDF',
            '/path/to/file.docx',
            '/path/to/another.txt',
            '/path/to/noextension'
        ]
        
        result = extract_file_types(files)
        expected = ['docx', 'pdf', 'txt']  # sorted, lowercase, unique
        
        self.assertEqual(result, expected)

    def test_extract_file_types_empty_list(self):
        """Test extracting file types from empty list"""
        result = extract_file_types([])
        expected = []
        self.assertEqual(result, expected)

    def test_get_collaborators(self):
        """Test get_collaborators function"""
        # This function currently returns None as it needs Google Drive API
        result = get_collaborators('test123')
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()