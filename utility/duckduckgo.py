from langchain_community.document_loaders import AsyncHtmlLoader
from langchain_community.document_transformers import Html2TextTransformer
from langchain.tools import DuckDuckGoSearchResults
import re

search = DuckDuckGoSearchResults(source="cardiff.ac.uk")

# This should take in user input later
result = search.run("applied software engineering site:cardiff.ac.uk")

# get rid of '[' and ']' to extract the link easier
clean_result = result.replace('[', '').replace(']', '')
links = re.findall(r'link: (.*?),', clean_result)
print(links)

# Uses AsyncHtmlLoader to make asynchronous HTTP requests to fetch the data
loader = AsyncHtmlLoader(links)
data = loader.load()

# Uses HTML2Text to convert HTML content into plain text
html2text = Html2TextTransformer()
data_transformed = html2text.transform_documents(data)

# Remove all the new line (\n) to clean up
for doc in data_transformed:
    cleanup_data = doc.page_content.replace('\n', '')
    print(cleanup_data)
