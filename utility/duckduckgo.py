from langchain_community.document_loaders import AsyncHtmlLoader
from langchain_community.document_transformers import Html2TextTransformer
from langchain.tools import DuckDuckGoSearchResults
import re

search = DuckDuckGoSearchResults(source="cardiff.ac.uk")
result = search.run("applied software engineering site:cardiff.ac.uk")
clean_result = result.replace('[', '').replace(']', '')
links = re.findall(r'link: (.*?),', clean_result)
print(links)

loader = AsyncHtmlLoader(links)
data = loader.load()

html2text = Html2TextTransformer()
data_transformed = html2text.transform_documents(data)
for doc in data_transformed:
    cleanup_data = doc.page_content.replace('\n', '')
    print(cleanup_data)