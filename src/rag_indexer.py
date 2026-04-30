from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from typing import List, Dict
import os


def index_signals(signals: List[Dict]) -> None:
    search_key = os.getenv("AZURE_SEARCH_API_KEY")
    credential = AzureKeyCredential(search_key) if search_key else DefaultAzureCredential()

    search_client = SearchClient(
        endpoint=os.environ["AZURE_SEARCH_ENDPOINT"],
        index_name=os.environ["AZURE_SEARCH_INDEX"],
        credential=credential
    )

    documents = [
        {"id": str(i), "signal": str(signal)}
        for i, signal in enumerate(signals)
    ]

    search_client.upload_documents(documents)