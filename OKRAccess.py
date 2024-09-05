from typing import Dict, List, Any, Optional, Union, Tuple
from typing_extensions import Annotated
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from enum import Enum
import json
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from PydanticTaskModels import *



################################################################################
##
#     ______    __   ___   _______    ________  
#    /    " \  |/"| /  ") /"      \  /"       ) 
#   // ____  \ (: |/   / |:        |(:   \___/  
#  /  /    ) :)|    __/  |_____/   ) \___  \    
# (: (____/ // (// _  \   //      /   __/  \\   
#  \        /  |: | \  \ |:  __   \  /" \   :)  
#   \"_____/   (__|  \__)|__|  \___)(_______/   
                                              


# Updated GraphQL mutations and queries
CREATE_OKR = gql("""
mutation CreateOKR($input: CreateOKRInput!) {
    createOKR(input: $input) {
        id
        title
        description
        createdAt
        updatedAt
    }
}
""")

LIST_OKRS = gql("""
query ListOKRs {
    listOKRS {
        items {
            id
            title
            description
            createdAt
            updatedAt
        }
    }
}
""")

from typing import List
from datetime import datetime

class OKR:
    def __init__(self, client):
        self.client = client

    def create_okr(self, okr_input: OKRCreate) -> OKROut:
        """
        Create a new OKR and send it to the GraphQL API.
        
        Args:
            okr_input (OKRCreate): The input data for creating a new OKR.
        
        Returns:
            OKROut: The created OKR.
        """
        variables = {
            "input": {
                "title": okr_input.title,
                "description": okr_input.description,
            }
        }
        
        result = self.client.execute(CREATE_OKR, variable_values=variables)
        
        created_okr = result['createOKR']
        
        return OKROut(
            id=created_okr['id'],
            title=created_okr['title'],
            description=created_okr['description'],
            createdAt=datetime.fromisoformat(created_okr['createdAt'].replace('Z', '+00:00')),
            updatedAt=datetime.fromisoformat(created_okr['updatedAt'].replace('Z', '+00:00'))
        )

    def list_okrs(self, nm: NullModel) -> OKROutList:
        """
        List all OKRs from the GraphQL API.    
        Returns:
            OKROutList: A Pydantic model containing a list of all OKRs.
        """
        result = self.client.execute(LIST_OKRS)    
        okrs = result['listOKRS']['items']
        okr_list = [
            OKROut(
                id=okr['id'],
                title=okr['title'],
                description=okr['description'],
                createdAt=datetime.fromisoformat(okr['createdAt'].replace('Z', '+00:00')),
                updatedAt=datetime.fromisoformat(okr['updatedAt'].replace('Z', '+00:00'))
            ) for okr in okrs
        ]
        return OKROutList(okrs=okr_list)
