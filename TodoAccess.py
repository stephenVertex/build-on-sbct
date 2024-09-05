from typing import Dict, List, Any, Optional, Union, Tuple
from typing_extensions import Annotated
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from enum import Enum
import json
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from PydanticTaskModels import *

# GraphQL mutations
CREATE_TODO = gql("""
mutation CreateTodo($input: CreateTodoInput!) {
    createTodo(input: $input) {
        id
        content
        createdAt
        updatedAt
    }
}
""")

class Todo:
    def __init__(self, client):
        self.client = client

    def create_todo(self, todo_input: TodoCreate) -> TodoOut:
        """
        Create a new Todo task and send it to the GraphQL API.
        
        Args:
            todo_input (TodoCreate): The input data for creating a new Todo.
        
        Returns:
            TodoOut: The created Todo task.
        """
        variables = {
            "input": {
                "content": todo_input.content
            }
        }
        
        result = self.client.execute(CREATE_TODO, variable_values=variables)
        
        created_todo = result['createTodo']
        
        return TodoOut(
            id=created_todo['id'],
            content=created_todo['content'],
            createdAt=datetime.fromisoformat(created_todo['createdAt'].replace('Z', '+00:00')),
            updatedAt=datetime.fromisoformat(created_todo['updatedAt'].replace('Z', '+00:00'))
        )
