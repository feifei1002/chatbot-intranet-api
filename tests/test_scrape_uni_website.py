import pytest
from unittest.mock import patch, Mock
from utils.scrape_uni_website import duckduckgo_search


@pytest.mark.asyncio
async def test_duckduckgo_search():
    # Mock external dependencies
    mock_results = Mock()

    # Set up patching for DuckDuckGoSearchAPIWrapper and DuckDuckGoSearchResults
    with patch('utils.scrape_uni_website.duckduckgo_search'):
        # Set up the expected values
        query = ("What are the tuition for studying "
                 "computer science at Cardiff University?")
        expected_result = ["https://www.cardiff.ac.uk/study/undergraduate"
                           "/courses/course/computer-science-bsc"]

        # Mock the run method of DuckDuckGoSearchResults
        mock_results.run.return_value = str(expected_result)

        # Call the function
        result = await duckduckgo_search(query)

        print("Expected result: " + expected_result[0])
        normalized_expected_result = [result[0]]
        print("Normalized expected result: " + normalized_expected_result[0])

        # Check the return value
        assert expected_result == normalized_expected_result
