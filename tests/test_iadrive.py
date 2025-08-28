import unittest
import os
import shutil
import json
import time
import requests_mock
import tempfile
import logging
from unittest.mock import patch, MagicMock, mock_open
import urllib.request

from iadrive.core import IAdrive
from iadrive import __version__


SCANNER = f'IAdrive Google Drive File Mirroring Application {__version__}'

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


class MockUrllibRequest:
    """Mock for urllib.request to simulate Google Docs downloads"""
    
    @staticmethod
    def urlretrieve(url, filename):
        """Mock urlretrieve for Google Docs export"""
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Create mock file content based on format
        ext = os.path.splitext(filename)[1].lower()
        if ext == '.pdf':
            content = b'%PDF-1.4 Mock PDF content'
        elif ext == '.docx':
            content = b'PK\x03\x04 Mock DOCX content'  # DOCX files start with PK
        elif ext == '.txt':
            content = b'Mock text content from Google Doc'
        elif ext == '.html':
            content = b'<html><body>Mock HTML content</body></html>'
        elif ext == '.csv':
            content = b'Column1,Column2,Column3\nValue1,Value2,Value3'
        else:
            content = f'Mock {ext} content'.encode('utf-8')
        
        with open(filename, 'wb') as f:
            f.write(content)
    
    @staticmethod
    def urlopen(url, timeout=None):
        """Mock urlopen for getting document titles"""
        class MockResponse:
            def read(self):
                if 'document' in url:
                    return b'<html><head><title>Test Document - Google Docs</title></head></html>'
                elif 'spreadsheets' in url:
                    return b'<html><head><title>Test Spreadsheet - Google Sheets</title></head></html>'
                elif 'presentation' in url:
                    return b'<html><head><title>Test Presentation - Google Slides</title></head></html>'
                return b'<html><head><title>Untitled Document</title></head></html>'
            
            def __enter__(self):
                return self
            
            def __exit__(self, *args):
                pass
        
        return MockResponse()


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

    # Original Google Drive tests
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

    def test_is_folder_url(self):
        """Test folder URL detection"""
        folder_url = 'https://drive.google.com/drive/folders/1-0axLqCuOUNbBIe3Cz6Y1KojGg4iXg1h'
        file_url = 'https://drive.google.com/file/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit'
        
        self.assertTrue(self.iadrive.is_folder_url(folder_url))
        self.assertFalse(self.iadrive.is_folder_url(file_url))

    # Google Docs specific tests
    def test_is_google_docs_url(self):
        """Test Google Docs URL detection"""
        docs_urls = [
            'https://docs.google.com/document/d/1abc123/edit',
            'https://docs.google.com/spreadsheets/d/1abc123/edit',
            'https://docs.google.com/presentation/d/1abc123/edit'
        ]
        drive_url = 'https://drive.google.com/file/d/1abc123'
        
        for url in docs_urls:
            self.assertTrue(self.iadrive.is_google_docs_url(url))
        
        self.assertFalse(self.iadrive.is_google_docs_url(drive_url))

    def test_get_google_docs_type(self):
        """Test getting Google Docs type"""
        test_cases = [
            ('https://docs.google.com/document/d/1abc123/edit', 'document'),
            ('https://docs.google.com/spreadsheets/d/1abc123/edit', 'spreadsheets'),
            ('https://docs.google.com/presentation/d/1abc123/edit', 'presentation'),
            ('https://drive.google.com/file/d/1abc123', None)
        ]
        
        for url, expected in test_cases:
            result = self.iadrive.get_google_docs_type(url)
            self.assertEqual(result, expected)

    def test_extract_docs_id(self):
        """Test extracting Google Docs ID"""
        test_cases = [
            ('https://docs.google.com/document/d/1abc123def456/edit', '1abc123def456'),
            ('https://docs.google.com/spreadsheets/d/1xyz789/edit#gid=0', '1xyz789'),
            ('https://docs.google.com/presentation/d/1pqr456/edit#slide=1', '1pqr456')
        ]
        
        for url, expected in test_cases:
            result = self.iadrive.extract_docs_id(url)
            self.assertEqual(result, expected)

    def test_extract_docs_id_invalid_url(self):
        """Test extracting docs ID from invalid URL"""
        url = 'https://example.com/invalid'
        with self.assertRaises(ValueError):
            self.iadrive.extract_docs_id(url)

    @patch('iadrive.core.urllib.request', MockUrllibRequest)
    def test_download_google_doc_all_formats(self):
        """Test downloading Google Doc with all formats automatically"""
        url = 'https://docs.google.com/document/d/1abc123/edit'
        doc_id = '1abc123'
        doc_type = 'document'
        
        download_path, result_id, files = self.iadrive.download_google_doc(url, doc_id, doc_type)
        
        self.assertEqual(result_id, doc_id)
        self.assertTrue(os.path.exists(download_path))
        # Should have all 7 document formats: pdf, docx, odt, rtf, txt, html, epub
        self.assertEqual(len(files), 7)
        
        # Check that all expected formats are present
        extensions = [os.path.splitext(f)[1].lower() for f in files]
        expected_extensions = ['.pdf', '.docx', '.odt', '.rtf', '.txt', '.html', '.epub']
        for ext in expected_extensions:
            self.assertIn(ext, extensions, f"Missing format: {ext}")
        
        # Check that files were created and have content
        for file_path in files:
            self.assertTrue(os.path.exists(file_path))
            self.assertGreater(os.path.getsize(file_path), 0)

    @patch('iadrive.core.urllib.request', MockUrllibRequest)
    def test_download_google_sheet_all_formats(self):
        """Test downloading Google Spreadsheet with all formats automatically"""
        url = 'https://docs.google.com/spreadsheets/d/1abc123/edit'
        doc_id = '1abc123'
        doc_type = 'spreadsheets'
        
        download_path, result_id, files = self.iadrive.download_google_doc(url, doc_id, doc_type)
        
        self.assertEqual(result_id, doc_id)
        # Should have all 6 spreadsheet formats: xlsx, ods, pdf, csv, tsv, html
        self.assertEqual(len(files), 6)
        
        # Check that all expected formats are present
        extensions = [os.path.splitext(f)[1].lower() for f in files]
        expected_extensions = ['.xlsx', '.ods', '.pdf', '.csv', '.tsv', '.html']
        for ext in expected_extensions:
            self.assertIn(ext, extensions, f"Missing format: {ext}")

    @patch('iadrive.core.urllib.request', MockUrllibRequest)
    def test_download_google_presentation_all_formats(self):
        """Test downloading Google Presentation with all formats automatically"""
        url = 'https://docs.google.com/presentation/d/1abc123/edit'
        doc_id = '1abc123'
        doc_type = 'presentation'
        
        download_path, result_id, files = self.iadrive.download_google_doc(url, doc_id, doc_type)
        
        self.assertEqual(result_id, doc_id)
        # Should have all 7 presentation formats: pdf, pptx, odp, txt, jpeg, png, svg
        self.assertEqual(len(files), 7)
        
        # Check that all expected formats are present
        extensions = [os.path.splitext(f)[1].lower() for f in files]
        expected_extensions = ['.pdf', '.pptx', '.odp', '.txt', '.jpeg', '.png', '.svg']
        for ext in expected_extensions:
            self.assertIn(ext, extensions, f"Missing format: {ext}")

    @patch('iadrive.core.urllib.request', MockUrllibRequest)
    def test_get_google_docs_title(self):
        """Test getting Google Docs title"""
        test_cases = [
            ('https://docs.google.com/document/d/1abc123/edit', 'Test Document'),
            ('https://docs.google.com/spreadsheets/d/1abc123/edit', 'Test Spreadsheet'),
            ('https://docs.google.com/presentation/d/1abc123/edit', 'Test Presentation')
        ]
        
        for url, expected in test_cases:
            result = self.iadrive.get_google_docs_title(url, '1abc123')
            self.assertEqual(result, expected)

    def test_create_metadata_google_docs(self):
        """Test metadata creation for Google Docs"""
        # Create test files
        test_doc_path = os.path.join(self.test_dir, 'Test Document.pdf')
        with open(test_doc_path, 'w') as f:
            f.write('test pdf content')
        
        file_map = {'Test Document.pdf': test_doc_path}
        drive_id = 'test123'
        url = 'https://docs.google.com/document/d/test123/edit'
        
        metadata = self.iadrive.create_metadata(
            file_map, drive_id, url, None, is_google_docs=True, doc_type='document'
        )
        
        self.assertEqual(metadata['title'], 'Test Document')
        self.assertEqual(metadata['mediatype'], 'texts')
        self.assertEqual(metadata['collection'], 'opensource_media')
        self.assertEqual(metadata['doctype'], 'document')
        self.assertIn('document', metadata['subject'])
        self.assertIn('Google Document exported', metadata['description'])

    @patch('iadrive.core.internetarchive')
    def test_upload_to_ia_google_docs(self, mock_ia):
        """Test uploading Google Docs to Internet Archive"""
        # Mock IA item
        mock_item = MagicMock()
        mock_item.exists = False
        mock_ia.get_item.return_value = mock_item
        
        # Create test file
        test_file = os.path.join(self.test_dir, 'test.pdf')
        with open(test_file, 'w') as f:
            f.write('test')
        
        file_map = {'test.pdf': test_file}
        drive_id = 'test123'
        metadata = {'title': 'Test Doc', 'mediatype': 'texts'}
        
        identifier, result_metadata = self.iadrive.upload_to_ia(
            file_map, drive_id, metadata, is_google_docs=True
        )
        
        self.assertEqual(identifier, 'docs-test123')  # docs- prefix for Google Docs
        self.assertEqual(result_metadata, metadata)
        mock_item.upload.assert_called_once()

    @patch('iadrive.core.gdown', MockGdown)
    def test_download_drive_content_file(self):
        """Test downloading a single file (original functionality)"""
        url = 'https://drive.google.com/file/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit'
        
        download_path, drive_id, files = self.iadrive.download_drive_content(url)
        
        self.assertEqual(drive_id, '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms')
        self.assertTrue(os.path.exists(download_path))
        self.assertIsNone(files)  # Regular drive downloads don't return file list

    @patch('iadrive.core.urllib.request', MockUrllibRequest)
    def test_download_drive_content_google_docs(self):
        """Test downloading Google Docs"""
        url = 'https://docs.google.com/document/d/1abc123/edit'
        
        download_path, drive_id, files = self.iadrive.download_drive_content(url)
        
        self.assertEqual(drive_id, '1abc123')
        self.assertTrue(os.path.exists(download_path))
        self.assertIsNotNone(files)  # Google Docs downloads return file list
        self.assertGreater(len(files), 0)

    def test_docs_formats_structure(self):
        """Test that docs_formats structure is correct"""
        # Check that all document types are present
        self.assertIn('document', self.iadrive.docs_formats)
        self.assertIn('spreadsheets', self.iadrive.docs_formats)
        self.assertIn('presentation', self.iadrive.docs_formats)
        
        # Check some expected formats
        self.assertIn('pdf', self.iadrive.docs_formats['document'])
        self.assertIn('xlsx', self.iadrive.docs_formats['spreadsheets'])
        self.assertIn('pptx', self.iadrive.docs_formats['presentation'])
        
        # Ensure we have all the expected formats for comprehensive export
        doc_formats = self.iadrive.docs_formats['document']
        self.assertEqual(len(doc_formats), 7)  # pdf, docx, odt, rtf, txt, html, epub
        
        sheet_formats = self.iadrive.docs_formats['spreadsheets']
        self.assertEqual(len(sheet_formats), 6)  # xlsx, ods, pdf, csv, tsv, html
        
        pres_formats = self.iadrive.docs_formats['presentation']
        self.assertEqual(len(pres_formats), 7)  # pdf, pptx, odp, txt, jpeg, png, svg


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
    def test_archive_drive_url_full_workflow_traditional(self, mock_ia):
        """Test the complete workflow for traditional Google Drive content"""
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
        self.assertEqual(metadata['mediatype'], 'data')
        mock_item.upload.assert_called_once()

    @patch('iadrive.core.urllib.request', MockUrllibRequest)
    @patch('iadrive.core.internetarchive')
    def test_archive_drive_url_full_workflow_google_docs(self, mock_ia):
        """Test the complete workflow for Google Docs"""
        # Mock IA session and item
        mock_session = MagicMock()
        mock_session.config = {'s3': {'access': 'test_key'}}
        mock_ia.get_session.return_value = mock_session
        
        mock_item = MagicMock()
        mock_item.exists = False
        mock_ia.get_item.return_value = mock_item
        
        url = 'https://docs.google.com/document/d/1abc123/edit'
        
        identifier, metadata = self.iadrive.archive_drive_url(url)
        
        self.assertEqual(identifier, 'docs-1abc123')
        self.assertEqual(metadata['title'], 'Test Document')
        self.assertEqual(metadata['originalurl'], url)
        self.assertEqual(metadata['mediatype'], 'texts')
        self.assertEqual(metadata['doctype'], 'document')
        self.assertEqual(metadata['filecount'], '7')
        mock_item.upload.assert_called_once()


if __name__ == '__main__':
    unittest.main()