import pytest
import II_2021 as ii



@pytest.mark.parametrize("test_input, expected", [(0, 0), (1, 1), (7, 1), (8, 1), (6, 0), (10, 0)])

def test_get_parity(test_input, expected):
    assert expected == ii.get_parity(test_input)



@pytest.mark.parametrize("test_input", ["a", "123411", "2asfdsah", "3", "   ", "dlksafu89%)(/(/!#"])
def test_parity(test_input):
    assert test_input == ii.check_parity(ii.add_parity(test_input))