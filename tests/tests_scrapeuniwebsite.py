import pytest
import os
from openai import OpenAI
from unittest.mock import patch, Mock
from utility.scrapeUniWebsite import duckduckgo_search

TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")
client = OpenAI(api_key=TOGETHER_API_KEY, base_url="https://api.together.xyz/v1")

print("TOGETHER API KEY: ", TOGETHER_API_KEY)


@pytest.mark.asyncio
async def test_duckduckgo_search():
    # Mock external dependencies
    mock_results = Mock()

    # Set up patching for DuckDuckGoSearchAPIWrapper and DuckDuckGoSearchResults
    with patch('utility.scrapeUniWebsite.DuckDuckGoSearchAPIWrapper'):
        with patch('utility.scrapeUniWebsite.DuckDuckGoSearchResults',
                   return_value=mock_results):
            # Set up the expected values
            query = "What are the tuition for study computer science at Cardiff University?"
            expected_result = ["https://www.cardiff.ac.uk/documents/2583013-fees-and-access-plan-2022-23"]

            # Mock the run method of DuckDuckGoSearchResults
            mock_results.run.return_value = str(expected_result)

            # Call the function
            result = await duckduckgo_search(query)

            print("Expected result: " + expected_result[0])
            normalized_expected_result = [result[0].replace("'", "")]

            # Assert that the function behaves as expected
            mock_results.run.assert_called_once_with(query)

            # Check the return value
            assert expected_result == normalized_expected_result
