from skatetrax.utils.common import minutes_to_hours, currency_usd

# run via: PYTHONPATH=. pytest tests/test_utils.py -v


class TestMinutesToHours:

    def test_exact_hour(self):
        @minutes_to_hours
        def f():
            return 60
        assert f() == {'hours': 1, 'minutes': 0.0}

    def test_fractional(self):
        @minutes_to_hours
        def f():
            return 90.5
        assert f() == {'hours': 1, 'minutes': 30.5}

    def test_zero(self):
        @minutes_to_hours
        def f():
            return 0
        assert f() == {'hours': 0, 'minutes': 0.0}

    def test_none_returns_zeros(self):
        @minutes_to_hours
        def f():
            return None
        assert f() == {'hours': 0, 'minutes': 0}

    def test_large_value(self):
        @minutes_to_hours
        def f():
            return 30700
        result = f()
        assert result['hours'] == 511
        assert result['minutes'] == 40.0

    def test_under_one_hour(self):
        @minutes_to_hours
        def f():
            return 45
        assert f() == {'hours': 0, 'minutes': 45.0}

    def test_multiple_exact_hours(self):
        @minutes_to_hours
        def f():
            return 180
        assert f() == {'hours': 3, 'minutes': 0.0}


class TestCurrencyUsd:

    def test_basic(self):
        @currency_usd
        def f():
            return 8.2
        assert f() == "8.20"

    def test_zero(self):
        @currency_usd
        def f():
            return 0
        assert f() == "0.00"

    def test_none_returns_zero(self):
        @currency_usd
        def f():
            return None
        assert f() == "0.00"

    def test_rounds_to_two_decimals(self):
        @currency_usd
        def f():
            return 23.456
        assert f() == "23.46"

    def test_whole_number(self):
        @currency_usd
        def f():
            return 100
        assert f() == "100.00"
