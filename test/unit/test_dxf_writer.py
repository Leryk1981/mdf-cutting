import unittest
from unittest.mock import MagicMock, patch, call
import ezdxf
from ezdxf.enums import TextEntityAlignment

# Assuming the packer module is in the PYTHONPATH
# If not, sys.path adjustments might be needed for standalone test runs,
# but for 'python -m unittest discover', this should work if tests are run from project root.
from packer.dxf_writer import (
    create_new_dxf,
    add_sheet_outline,
    add_detail_to_sheet,
    add_layout_filename_title,
    add_details_list
)
from packer.constants import (
    DEFAULT_TEXT_STYLE,
    DEFAULT_TEXT_HEIGHT,
    HEADER_TEXT_HEIGHT,
    BORDER_COLOR,
    TEXT_COLOR,
    DETAIL_TEXT_COLOR
    # DIMENSION_COLOR is not used by current dxf_writer functions
)

class TestDxfWriter(unittest.TestCase):

    def test_create_new_dxf(self):
        doc, msp = create_new_dxf()
        self.assertIsNotNone(doc)
        self.assertIsNotNone(msp)
        self.assertEqual(doc.header['$LUNITS'], 2)  # Decimal units
        self.assertEqual(doc.header['$INSUNITS'], 4) # Millimeters

    @patch('packer.dxf_writer.ezdxf.new')
    def test_create_new_dxf_mocked(self, mock_ezdxf_new):
        mock_doc = MagicMock()
        mock_msp = MagicMock()
        mock_ezdxf_new.return_value = mock_doc
        mock_doc.modelspace.return_value = mock_msp
        mock_doc.header = {} # Simulate header dict

        doc, msp = create_new_dxf()

        mock_ezdxf_new.assert_called_once_with(dxfversion='R2010')
        mock_doc.modelspace.assert_called_once()
        self.assertEqual(doc.header['$LUNITS'], 2)
        self.assertEqual(doc.header['$INSUNITS'], 4)
        self.assertEqual(doc, mock_doc)
        self.assertEqual(msp, mock_msp)

    def test_add_sheet_outline(self):
        mock_msp = MagicMock()
        sheet_length = 1000
        sheet_width = 500
        margin = 10

        add_sheet_outline(mock_msp, sheet_length, sheet_width, margin)

        expected_calls = [
            call(
                [(0, 0), (sheet_length, 0), (sheet_length, sheet_width), (0, sheet_width), (0, 0)],
                dxfattribs={'color': BORDER_COLOR, 'layer': 'Sheet Outline'}
            ),
            call(
                [(margin, margin), (sheet_length - margin, margin),
                 (sheet_length - margin, sheet_width - margin), (margin, sheet_width - margin), (margin, margin)],
                dxfattribs={'color': BORDER_COLOR, 'linetype': 'DASHED', 'layer': 'Working Area'}
            )
        ]
        mock_msp.add_lwpolyline.assert_has_calls(expected_calls, any_order=False)
        self.assertEqual(mock_msp.add_lwpolyline.call_count, 2)


    def test_add_detail_to_sheet_non_rotated(self):
        mock_msp = MagicMock()
        detail_data = {'part_id': 'Part1', 'length_mm': 100, 'width_mm': 50} # length_mm maps to width after kerf
        detail_rect = {'x': 10, 'y': 20, 'width': 105, 'height': 55, 'rotated': False} # width = 100+5, height = 50+5
        kerf = 5

        # Mock the add_text method to return a mock object that has a set_placement method
        mock_text_entity = MagicMock()
        mock_msp.add_text.return_value = mock_text_entity

        returned_info = add_detail_to_sheet(mock_msp, detail_data, detail_rect, kerf)

        actual_length = detail_rect['width'] - kerf # 100
        actual_width = detail_rect['height'] - kerf # 50

        # Check polyline for detail outline
        mock_msp.add_lwpolyline.assert_called_once_with(
            [(detail_rect['x'], detail_rect['y']),
             (detail_rect['x'] + actual_length, detail_rect['y']),
             (detail_rect['x'] + actual_length, detail_rect['y'] + actual_width),
             (detail_rect['x'], detail_rect['y'] + actual_width),
             (detail_rect['x'], detail_rect['y'])],
            dxfattribs={'color': TEXT_COLOR, 'layer': 'Details'}
        )

        # Check text for detail ID and size
        expected_text_content = f"{detail_data['part_id']} ({actual_length:.0f}x{actual_width:.0f})"
        text_x = detail_rect['x'] + actual_length / 2
        text_y = detail_rect['y'] + actual_width / 2

        mock_msp.add_text.assert_called_once_with(
            expected_text_content,
            dxfattribs={
                'style': DEFAULT_TEXT_STYLE,
                'height': DEFAULT_TEXT_HEIGHT,
                'color': DETAIL_TEXT_COLOR,
                'layer': 'Detail Text'
            }
        )
        mock_text_entity.set_placement.assert_called_once_with(
            (text_x, text_y),
            align=TextEntityAlignment.MIDDLE_CENTER
        )

        self.assertEqual(returned_info, {'name': 'Part1', 'size': '100x50'})

    def test_add_detail_to_sheet_rotated(self):
        mock_msp = MagicMock()
        # Original detail: length=50, width=100. Packed as: width=105 (orig_height+kerf), height=55 (orig_length+kerf)
        detail_data = {'part_id': 'PartR', 'length_mm': 50, 'width_mm': 100}
        detail_rect = {'x': 10, 'y': 20, 'width': 105, 'height': 55, 'rotated': True} # Simulating rotation
        kerf = 5

        mock_text_entity = MagicMock()
        mock_msp.add_text.return_value = mock_text_entity

        returned_info = add_detail_to_sheet(mock_msp, detail_data, detail_rect, kerf)

        # Actual dimensions of the part as placed (after kerf removal)
        # For a rotated part, rect.width (packed) corresponds to original height + kerf
        # and rect.height (packed) corresponds to original length + kerf
        actual_length_on_sheet = detail_rect['width'] - kerf  # This is 100 (original width_mm)
        actual_width_on_sheet = detail_rect['height'] - kerf # This is 50 (original length_mm)

        mock_msp.add_lwpolyline.assert_called_once() # Basic check, details in previous test

        expected_text_content = f"{detail_data['part_id']} ({actual_length_on_sheet:.0f}x{actual_width_on_sheet:.0f})"
        mock_msp.add_text.assert_called_once_with(
            expected_text_content,
            dxfattribs=unittest.mock.ANY # Check other args in specific tests
        )
        mock_text_entity.set_placement.assert_called_once()

        self.assertEqual(returned_info, {'name': 'PartR', 'size': f"{actual_length_on_sheet:.0f}x{actual_width_on_sheet:.0f}"})


    def test_add_layout_filename_title(self):
        mock_msp = MagicMock()
        mock_text_entity = MagicMock()
        mock_msp.add_text.return_value = mock_text_entity
        sheet_length = 1000
        sheet_width = 500
        filename = "test_layout.dxf"

        add_layout_filename_title(mock_msp, sheet_length, sheet_width, filename)

        mock_msp.add_text.assert_called_once_with(
            filename,
            dxfattribs={
                'style': DEFAULT_TEXT_STYLE,
                'height': HEADER_TEXT_HEIGHT,
                'color': TEXT_COLOR,
                'layer': 'Title'
            }
        )
        mock_text_entity.set_placement.assert_called_once_with(
            (sheet_length / 2, sheet_width + HEADER_TEXT_HEIGHT * 2),
            align=TextEntityAlignment.MIDDLE_CENTER
        )

    def test_add_details_list(self):
        mock_msp = MagicMock()
        # Mock the add_text method to return a mock object that has a set_placement method
        # We'll need it to be called multiple times, so we use side_effect
        mock_text_entities = [MagicMock() for _ in range(3)] # Title + 2 details
        mock_msp.add_text.side_effect = mock_text_entities

        sheet_width = 500 # Not directly used by add_text mock, but passed to function
        details = [
            {'name': 'PartA', 'size': '100x50'},
            {'name': 'PartB', 'size': '200x75'}
        ]

        add_details_list(mock_msp, sheet_width, details)

        self.assertEqual(mock_msp.add_text.call_count, 3) # Title + 2 details

        # Check title
        call_args_title = mock_msp.add_text.call_args_list[0]
        self.assertEqual(call_args_title[0][0], "Список деталей:")
        self.assertEqual(call_args_title[1]['dxfattribs']['height'], DEFAULT_TEXT_HEIGHT)

        # Check placement of title (assuming default list_position_y and text_height)
        expected_y_title = - (DEFAULT_TEXT_HEIGHT * (len(details) + 2))
        mock_text_entities[0].set_placement.assert_called_once_with(
            (0, expected_y_title),
            align=TextEntityAlignment.BOTTOM_LEFT
        )

        # Check first detail
        call_args_detail1 = mock_msp.add_text.call_args_list[1]
        self.assertEqual(call_args_detail1[0][0], "PartA - 100x50")

        # Check placement of first detail
        expected_y_detail1 = expected_y_title - DEFAULT_TEXT_HEIGHT * 1.5
        mock_text_entities[1].set_placement.assert_called_once_with(
            (0, expected_y_detail1),
            align=TextEntityAlignment.BOTTOM_LEFT
        )

        # Check second detail
        call_args_detail2 = mock_msp.add_text.call_args_list[2]
        self.assertEqual(call_args_detail2[0][0], "PartB - 200x75")

        # Check placement of second detail
        expected_y_detail2 = expected_y_detail1 - DEFAULT_TEXT_HEIGHT
        mock_text_entities[2].set_placement.assert_called_once_with(
            (0, expected_y_detail2),
            align=TextEntityAlignment.BOTTOM_LEFT
        )

    def test_add_details_list_custom_position_and_height(self):
        mock_msp = MagicMock()
        mock_text_entities = [MagicMock(), MagicMock()] # Title + 1 detail
        mock_msp.add_text.side_effect = mock_text_entities

        sheet_width = 600
        details = [{'name': 'TestP', 'size': '30x30'}]
        custom_y = 100
        custom_text_height = 15

        add_details_list(mock_msp, sheet_width, details, list_position_y=custom_y, text_height=custom_text_height)

        self.assertEqual(mock_msp.add_text.call_count, 2)

        # Check title with custom height
        call_args_title = mock_msp.add_text.call_args_list[0]
        self.assertEqual(call_args_title[1]['dxfattribs']['height'], custom_text_height)
        mock_text_entities[0].set_placement.assert_called_once_with(
            (0, custom_y), align=TextEntityAlignment.BOTTOM_LEFT
        )

        # Check detail with custom height and position
        expected_y_detail = custom_y - custom_text_height * 1.5
        call_args_detail = mock_msp.add_text.call_args_list[1]
        self.assertEqual(call_args_detail[1]['dxfattribs']['height'], custom_text_height)
        mock_text_entities[1].set_placement.assert_called_once_with(
            (0, expected_y_detail), align=TextEntityAlignment.BOTTOM_LEFT
        )

if __name__ == '__main__':
    unittest.main()
