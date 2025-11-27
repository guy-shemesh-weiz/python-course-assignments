from logic import calc_response


def test_exact_match():
    dig_num = 4
    expected_response = "*" * dig_num
    for i in range(10**dig_num):
        assert expected_response == calc_response(i, i, dig_num)


def test_no_match():
    dig_num = 4
    expected_response = ""
    assert expected_response == calc_response(10, 5555, dig_num)
    assert expected_response == calc_response(9999, 8888, dig_num)
    assert expected_response == calc_response(6789, 1234, dig_num)


def test_partial_match():
    dig_num = 4
    assert "**++" == calc_response(1268, 6218, dig_num)
    assert "**++" == calc_response(268, 6208, dig_num)
    assert "+" == calc_response(2, 6211, dig_num)
    assert "*" == calc_response(2, 6882, dig_num)
