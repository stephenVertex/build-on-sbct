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

import os


ENDPOINT = os.environ["BOSBCT_ENDPOINT"] 
API_KEY  = os.environ["BOSBCT_API_KEY"]



transport = RequestsHTTPTransport(
    url=ENDPOINT,
    headers={'x-api-key': API_KEY},
    use_json=True,
)

client = Client(transport=transport, fetch_schema_from_transport=True)
task_client = Task(client)
todo_client = Todo(client)
okr_client  = OKR(client)


