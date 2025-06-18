import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
from pandas.testing import assert_frame_equal

# Assuming 'packer' is in PYTHONPATH
from packer.utils import (
    load_and_prepare_data,
    read_csv_files,
    validate_dataframes,
    preprocess_dataframes,
    check_critical_values
)
from packer.constants import DETAILS_REQUIRED_COLUMNS, MATERIALS_REQUIRED_COLUMNS, SUPPORTED_ENCODINGS

class TestUtilsLoadAndPrepareData(unittest.TestCase):

    def _create_mock_details_df(self, data=None):
        if data is None:
            data = {
                'part_id': ['P1', 'P2'],
                'length_mm': [100.0, 200.0],
                'width_mm': [50.0, 75.0],
                'quantity': [10, 5],
                'thickness_mm': [18.0, 18.0],
                'material': ['WOOD', 'WOOD'],
                'bevel_type': ['None', 'None'],
                'order_id': ['O1', 'O2'],
                'bevel_offset_mm': [0.0,0.0],
                'f_long': [0,0],
                'f_short': [0,0],
            }
        df = pd.DataFrame(data)
        # Ensure all required columns are present, even if with default/None values
        for col in DETAILS_REQUIRED_COLUMNS:
            if col not in df.columns:
                df[col] = 0 # Or appropriate default
        if 'material' not in df.columns: # Explicitly ensure material as it's often defaulted
             df['material'] = 'S'
        return df

    def _create_mock_materials_df(self, data=None):
        if data is None:
            data = {
                'sheet_name': ['Sheet1', 'Remnant1'],
                'sheet_length_mm': [2440.0, 1000.0],
                'sheet_width_mm': [1220.0, 500.0],
                'total_quantity': [10, 1],
                'thickness_mm': [18.0, 18.0],
                'material': ['WOOD', 'WOOD'],
                'is_remnant': [False, True],
                'remnant_id': [None, 'R1']
            }
        df = pd.DataFrame(data)
        for col in MATERIALS_REQUIRED_COLUMNS:
            if col not in df.columns:
                df[col] = 0 # Or appropriate default
        if 'material' not in df.columns: # Explicitly ensure material
             df['material'] = 'S'
        if 'remnant_id' not in df.columns:
            df['remnant_id'] = None
        if 'is_remnant' not in df.columns:
            df['is_remnant'] = False

        return df

    @patch('packer.utils.read_csv_files')
    @patch('packer.utils.validate_dataframes')
    @patch('packer.utils.preprocess_dataframes')
    @patch('packer.utils.check_critical_values')
    def test_load_and_prepare_data_success(self, mock_check_critical, mock_preprocess, mock_validate, mock_read_csv):
        mock_details = self._create_mock_details_df()
        mock_materials = self._create_mock_materials_df()

        # Processed DFs (can be same as mock_details if preprocess doesn't change them, or different)
        processed_details = mock_details.copy()
        processed_materials = mock_materials.copy()
        # Simulate material column processing by preprocess_dataframes
        processed_details['material'] = processed_details['material'].astype(str).str.upper().replace('', 'S').fillna('S')
        processed_materials['material'] = processed_materials['material'].astype(str).str.upper().replace('', 'S').fillna('S')


        mock_read_csv.return_value = (mock_details, mock_materials)
        mock_validate.return_value = (True, [], [])
        mock_preprocess.return_value = (processed_details, processed_materials)
        mock_check_critical.return_value = True

        details_df, materials_df, error_message = load_and_prepare_data(
            "dummy_details.csv", "dummy_materials.csv",
            DETAILS_REQUIRED_COLUMNS, MATERIALS_REQUIRED_COLUMNS, SUPPORTED_ENCODINGS
        )

        self.assertIsNone(error_message)
        self.assertIsNotNone(details_df)
        self.assertIsNotNone(materials_df)
        assert_frame_equal(details_df, processed_details)
        assert_frame_equal(materials_df, processed_materials)

        mock_read_csv.assert_called_once_with("dummy_details.csv", "dummy_materials.csv", SUPPORTED_ENCODINGS)
        mock_validate.assert_called_once_with(mock_details, mock_materials, DETAILS_REQUIRED_COLUMNS, MATERIALS_REQUIRED_COLUMNS)
        mock_preprocess.assert_called_once_with(mock_details, mock_materials)
        mock_check_critical.assert_called_once_with(processed_details, processed_materials)

    @patch('packer.utils.read_csv_files')
    def test_load_and_prepare_data_read_csv_fails(self, mock_read_csv):
        mock_read_csv.return_value = (None, None)

        details_df, materials_df, error_message = load_and_prepare_data(
            "dummy_details.csv", "dummy_materials.csv",
            DETAILS_REQUIRED_COLUMNS, MATERIALS_REQUIRED_COLUMNS, SUPPORTED_ENCODINGS
        )
        self.assertIsNotNone(error_message)
        self.assertIsNone(details_df)
        self.assertIsNone(materials_df)
        self.assertIn("Failed to read one or both CSV files", error_message)

    @patch('packer.utils.read_csv_files')
    @patch('packer.utils.validate_dataframes')
    def test_load_and_prepare_data_validate_fails(self, mock_validate, mock_read_csv):
        mock_details = self._create_mock_details_df()
        mock_materials = self._create_mock_materials_df()
        mock_read_csv.return_value = (mock_details, mock_materials)
        mock_validate.return_value = (False, ['missing_col_detail'], ['missing_col_material'])

        details_df, materials_df, error_message = load_and_prepare_data(
            "dummy_details.csv", "dummy_materials.csv",
            DETAILS_REQUIRED_COLUMNS, MATERIALS_REQUIRED_COLUMNS, SUPPORTED_ENCODINGS
        )
        self.assertIsNotNone(error_message)
        self.assertIsNone(details_df)
        self.assertIsNone(materials_df)
        self.assertIn("Data validation failed", error_message)
        self.assertIn("missing_col_detail", error_message)
        self.assertIn("missing_col_material", error_message)

    @patch('packer.utils.read_csv_files')
    @patch('packer.utils.validate_dataframes')
    @patch('packer.utils.preprocess_dataframes')
    def test_load_and_prepare_data_preprocess_fails(self, mock_preprocess, mock_validate, mock_read_csv):
        mock_details = self._create_mock_details_df()
        mock_materials = self._create_mock_materials_df()
        mock_read_csv.return_value = (mock_details, mock_materials)
        mock_validate.return_value = (True, [], [])
        mock_preprocess.return_value = (None, None) # Simulate failure

        details_df, materials_df, error_message = load_and_prepare_data(
            "dummy_details.csv", "dummy_materials.csv",
            DETAILS_REQUIRED_COLUMNS, MATERIALS_REQUIRED_COLUMNS, SUPPORTED_ENCODINGS
        )
        self.assertIsNotNone(error_message)
        self.assertIsNone(details_df)
        self.assertIsNone(materials_df)
        self.assertIn("Data preprocessing failed", error_message)

    @patch('packer.utils.read_csv_files')
    @patch('packer.utils.validate_dataframes')
    @patch('packer.utils.preprocess_dataframes')
    @patch('packer.utils.check_critical_values')
    def test_load_and_prepare_data_check_critical_fails(self, mock_check_critical, mock_preprocess, mock_validate, mock_read_csv):
        mock_details = self._create_mock_details_df()
        mock_materials = self._create_mock_materials_df()
        processed_details = mock_details.copy() # Assume preprocess returns valid DFs
        processed_materials = mock_materials.copy()

        mock_read_csv.return_value = (mock_details, mock_materials)
        mock_validate.return_value = (True, [], [])
        mock_preprocess.return_value = (processed_details, processed_materials)
        mock_check_critical.return_value = False # Simulate failure

        details_df, materials_df, error_message = load_and_prepare_data(
            "dummy_details.csv", "dummy_materials.csv",
            DETAILS_REQUIRED_COLUMNS, MATERIALS_REQUIRED_COLUMNS, SUPPORTED_ENCODINGS
        )
        self.assertIsNotNone(error_message)
        self.assertIsNone(details_df)
        self.assertIsNone(materials_df)
        self.assertIn("Critical value check failed", error_message)

if __name__ == '__main__':
    unittest.main()
