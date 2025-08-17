import unittest
import os
import shutil
import json
import time
import requests_mock
import tempfile
import logging
from unittest.mock import patch, MagicMock

from iadrive.core import IAdrive
from iadrive import __version__


SCANNER = f'IAdrive Google Drive File Mirroring Application v{__version__}'

current_path = os.path.dirname(os.path.realpath(__file__))


def get_testfile_path(name):
    return os.path.join(current_path, 'test_iadrive_files', name)


class MockGdown:
    @staticmethod
    def download(url, output=None, quiet=True, fuzzy=True):
        """Mock gdown download for single files"""
        if not os.path.exists(output):
            os.makedirs(output, exist_ok=True)
        
        # Create a dummy file
        test_file = os.path.join(output, 'test_file.txt')
        with open(test_file, 'w') as f:
            f.write('Mock downloaded content')
        return test_file
    
    @staticmethod
    def download_folder(url, output=None, quiet=True):
        """Mock gdown download_folder for folders"""
        os.makedirs(output, exist_ok=True)
        
        # Create a folder structure
        folder_name = 'Test Folder'
        folder_path = os.path.join(output, folder_name)
        os.makedirs(folder_path, exist_ok=True)
        
        # Create some test files
        files = ['file1.txt', 'file2.pdf', 'subfolder/file3.docx']
        for file_path in files:
            full_path = os.path.join(folder_path, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as f:
                f.write(f'Mock content for {file_path}')


class IAdriveMockTests(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.iadrive = IAdrive(verbose=False, dir_path=self.test_dir)
        self.maxDiff = None

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_set_dir_path(self):
        """Test that directory is created correctly"""
        test_path = os.path.join(self.test_dir, 'custom_dir')
        iadrive = IAdrive(dir_path=test_path)
        
        self.assertTrue(os.path.exists(test_path))
        self.assertEqual(iadrive.dir_path, test_path)

    def test_logger_quiet_mode(self):
        """Test logger in quiet mode"""
        self.assertIsInstance(self.iadrive.logger, logging.Logger)
        self.assertEqual(self.iadrive.logger.level, logging.ERROR)

    def test_logger_verbose_mode(self):
        """Test logger in verbose mode"""
        iadrive = IAdrive(verbose=True, dir_path=self.test_dir)
        self.assertIsInstance(iadrive.logger, logging.Logger)

    def test_extract_drive_id_folder(self):
        """Test extracting drive ID from folder URL"""
        url = 'https://drive.google.com/drive/folders/1-0axLqCuOUNbBIe3Cz6Y1KojGg4iXg1h'
        result = self.iadrive.extract_drive_id(url)
        expected = '1-0axLqCuOUNbBIe3Cz6Y1KojGg4iXg1h'
        self.assertEqual(result, expected)

    def test_extract_drive_id_file(self):
        """Test extracting drive ID from file URL"""
        url = 'https://drive.google.com/file/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit'
        result = self.iadrive.extract_drive_id(url)
        expected = '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms'
        self.assertEqual(result, expected)

    def test_extract_drive_id_invalid_url(self):
        """Test extracting drive ID from invalid URL"""
        url = 'https://example.com/invalid'
        with self.assertRaises(ValueError):
            self.iadrive.extract_drive_id(url)

    def test_is_folder_url(self):
        """Test folder URL detection"""
        folder_url = 'https://drive.google.com/drive/folders/1-0axLqCuOUNbBIe3Cz6Y1KojGg4iXg1h'
        file_url = 'https://drive.google.com/file/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit'
        
        self.assertTrue(self.iadrive.is_folder_url(folder_url))
        self.assertFalse(self.iadrive.is_folder_url(file_url))

    @patch('iadrive.core.gdown', MockGdown)
    def test_download_drive_content_file(self):
        """Test downloading a single file"""
        url = 'https://drive.google.com/file/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit'
        
        download_path, drive_id = self.iadrive.download_drive_content(url)
        
        self.assertEqual(drive_id, '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms')
        self.assertTrue(os.path.exists(download_path))

    @patch('iadrive.core.gdown', MockGdown)
    def test_download_drive_content_folder(self):
        """Test downloading a folder"""
        url = 'https://drive.google.com/drive/folders/1-0axLqCuOUNbBIe3Cz6Y1KojGg4iXg1h'
        
        download_path, drive_id = self.iadrive.download_drive_content(url)
        
        self.assertEqual(drive_id, '1-0axLqCuOUNbBIe3Cz6Y1KojGg4iXg1h')
        self.assertTrue(os.path.exists(download_path))

    def test_get_file_list(self):
        """Test getting file list from directory"""
        # Create test directory structure
        test_dir = os.path.join(self.test_dir, 'test_files')
        os.makedirs(test_dir)
        
        files = ['file1.txt', 'subdir/file2.txt']
        for file_path in files:
            full_path = os.path.join(test_dir, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as f:
                f.write('test content')
        
        result = self.iadrive.get_file_list(test_dir)
        self.assertEqual(len(result), 2)

    def test_create_metadata_single_file(self):
        """Test metadata creation for single file"""
        # Create a test file
        test_file = os.path.join(self.test_dir, 'test.txt')
        with open(test_file, 'w') as f:
            f.write('test')
        
        files = [test_file]
        drive_id = 'test123'
        url = 'https://drive.google.com/file/d/test123'
        download_path = self.test_dir
        
        metadata = self.iadrive.create_metadata(files, drive_id, url, download_path)
        
        self.assertEqual(metadata['title'], 'test.txt')
        self.assertEqual(metadata['mediatype'], 'data')
        self.assertEqual(metadata['collection'], 'opensource')
        self.assertEqual(metadata['filecount'], '1')
        self.assertEqual(metadata['originalurl'], url)
        self.assertEqual(metadata['scanner'], SCANNER)

    def test_create_metadata_folder(self):
        """Test metadata creation for folder"""
        # Create test folder structure
        test_folder = os.path.join(self.test_dir, 'Test Folder')
        os.makedirs(test_folder)
        
        test_file = os.path.join(test_folder, 'file.txt')
        with open(test_file, 'w') as f:
            f.write('test')
        
        files = [test_file]
        drive_id = 'folder123'
        url = 'https://drive.google.com/drive/folders/folder123'
        download_path = self.test_dir
        
        metadata = self.iadrive.create_metadata(files, drive_id, url, download_path)
        
        self.assertEqual(metadata['title'], 'Test Folder')
        self.assertEqual(metadata['filecount'], '1')

    @patch('iadrive.core.internetarchive')
    def test_upload_to_ia(self, mock_ia):
        """Test uploading to Internet Archive"""
        # Mock IA item
        mock_item = MagicMock()
        mock_item.exists = False
        mock_ia.get_item.return_value = mock_item
        
        # Create test file
        test_file = os.path.join(self.test_dir, 'test.txt')
        with open(test_file, 'w') as f:
            f.write('test')
        
        files = [test_file]
        drive_id = 'test123'
        metadata = {'title': 'Test', 'mediatype': 'data'}
        
        identifier, result_metadata = self.iadrive.upload_to_ia(files, drive_id, metadata)
        
        self.assertEqual(identifier, 'drive-test123')
        self.assertEqual(result_metadata, metadata)
        mock_item.upload.assert_called_once()

    @patch('iadrive.core.internetarchive')
    def test_upload_to_ia_existing_item(self, mock_ia):
        """Test uploading when item already exists"""
        # Mock IA item that exists
        mock_item = MagicMock()
        mock_item.exists = True
        mock_ia.get_item.return_value = mock_item
        
        files = ['test.txt']
        drive_id = 'test123'
        metadata = {'title': 'Test'}
        
        identifier, result_metadata = self.iadrive.upload_to_ia(files, drive_id, metadata)
        
        self.assertEqual(identifier, 'drive-test123')
        mock_item.upload.assert_not_called()

    def test_check_dependencies_missing_gdown(self):
        """Test dependency check when gdown is missing"""
        with patch.dict('sys.modules', {'gdown': None}):
            with self.assertRaises(Exception) as cm:
                self.iadrive.check_dependencies()
            self.assertIn('Missing required package', str(cm.exception))

    @patch('iadrive.core.internetarchive')
    def test_check_dependencies_ia_not_configured(self, mock_ia):
        """Test dependency check when IA is not configured"""
        mock_session = MagicMock()
        mock_session.config = {'s3': {}}
        mock_ia.get_session.return_value = mock_session
        
        with self.assertRaises(Exception) as cm:
            self.iadrive.check_dependencies()
        self.assertIn('Internet Archive not configured', str(cm.exception))


class IAdriveIntegrationMockTest(unittest.TestCase):
    """Integration tests with mocked external dependencies"""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.iadrive = IAdrive(verbose=False, dir_path=self.test_dir)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    @patch('iadrive.core.gdown', MockGdown)
    @patch('iadrive.core.internetarchive')
    def test_archive_drive_url_full_workflow(self, mock_ia):
        """Test the complete workflow from URL to upload"""
        # Mock IA session and item
        mock_session = MagicMock()
        mock_session.config = {'s3': {'access': 'test_key'}}
        mock_ia.get_session.return_value = mock_session
        
        mock_item = MagicMock()
        mock_item.exists = False
        mock_ia.get_item.return_value = mock_item
        
        url = 'https://drive.google.com/drive/folders/1-0axLqCuOUNbBIe3Cz6Y1KojGg4iXg1h'
        
        identifier, metadata = self.iadrive.archive_drive_url(url)
        
        self.assertEqual(identifier, 'drive-1-0axlqcuounbbfe3cz6y1kojgg4ixg1h')
        self.assertEqual(metadata['title'], 'Test Folder')
        self.assertEqual(metadata['originalurl'], url)
        mock_item.upload.assert_called_once()