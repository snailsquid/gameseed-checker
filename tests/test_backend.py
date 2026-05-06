import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend import clean_text, parse_input, do_check


class TestCleanText:
    def test_normal_text(self):
        assert clean_text("Waguri") == "waguri"

    def test_with_whitespace(self):
        assert clean_text("  Waguri  ") == "waguri"

    def test_mixed_case(self):
        assert clean_text("WaguriGanteng") == "waguriganteng"

    def test_na_value(self):
        import pandas as pd
        assert clean_text(pd.NA) == ""


class TestParseInput:
    def test_single_name(self):
        result = parse_input("Waguri @Wagureng")
        assert len(result) == 1
        assert result[0]["original"] == "Waguri"
        assert result[0]["clean"] == "waguri"

    def test_multiple_names(self):
        result = parse_input("Waguri @Wagureng\nRentarou @BossTokoKue")
        assert len(result) == 2

    def test_name_with_dash_stripped(self):
        result = parse_input("Waguri- @Wagureng")
        assert len(result) == 1
        assert result[0]["original"] == "Waguri"

    def test_empty_lines_skipped(self):
        result = parse_input("Waguri @Wagureng\n\nRentarou @BossTokoKue")
        assert len(result) == 2

    def test_only_discord_stripped(self):
        result = parse_input("Waguri @Wagureng")
        assert "@" not in result[0]["original"]
        assert "@" not in result[0]["clean"]


class TestDoCheck:
    def test_registered_participant(self):
        import backend
        import pandas as pd

        mock_df = pd.DataFrame([
            {'Nama Lengkap': 'Waguri', 'Nama Asli': 'Waguri', 'Nama Clean': 'waguri', 'source': 'Mobile', 'Team': ''},
        ])
        backend.df_all = mock_df

        data = [{"original": "Waguri", "clean": "waguri"}]
        result = do_check(data)

        assert result['stats']['registered_count'] == 1
        assert result['stats']['not_registered_count'] == 0