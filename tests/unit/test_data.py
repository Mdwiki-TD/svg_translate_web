from src.main_app.data import get_slug_categories


class TestGetSlugCategories:
    def test_get_slug_categories(self):
        # Arrange
        expected_result = [
            "Category:Our World in Data - Medicine and Biotechnology",
            "Category:Our World in Data - Research and Development",
        ]

        # Act
        result = get_slug_categories("number-of-entries-in-biological-sequence-databases")

        result.sort()
        # Assert
        assert result == expected_result
