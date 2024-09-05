import argparse
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

from PydanticTaskModels import *
from TaskAccess import *
from TodoAccess import *
from OKRAccess  import *
ENDPOINT=  'https://3wwasfc2lvhdhcq4e3vnw5lb4m.appsync-api.us-east-1.amazonaws.com/graphql'
API_KEY= 'da2-cndisyx74verlbpnhb2kfsq6mq'

transport = RequestsHTTPTransport(
    url=ENDPOINT,
    headers={'x-api-key': API_KEY},
    use_json=True,
)

client = Client(transport=transport, fetch_schema_from_transport=True)
task_client = Task(client)
todo_client = Todo(client)
okr_client  = OKR(client)
