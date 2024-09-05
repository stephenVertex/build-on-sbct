from typing import Dict, List, Any, Optional, Union, Tuple
from typing_extensions import Annotated
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from enum import Enum
import json
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from PydanticTaskModels import TaskCreate, TaskOut, NullModel

################################################################################
##
##
#  ______   ______     ______     __  __     ______    
# /\__  _\ /\  __ \   /\  ___\   /\ \/ /    /\  ___\   
# \/_/\ \/ \ \  __ \  \ \___  \  \ \  _"-.  \ \___  \  
#    \ \_\  \ \_\ \_\  \/\_____\  \ \_\ \_\  \/\_____\ 
#     \/_/   \/_/\/_/   \/_____/   \/_/\/_/   \/_____/ 


CREATE_TASK = gql("""
mutation CreateTask($input: CreateTaskInput!) {
  createTask(input: $input) {
    id
    name
    description
    estimated_time_mins
    priority
    tags
    createdAt
    updatedAt
  }
}
""")

LIST_TASKS = gql("""
query ListTasks {
  listTasks {
    items {
      id
      name
      description
      estimated_time_mins
      priority
      tags
      createdAt
      updatedAt
    }
  }
}
""")

from typing import List
from datetime import datetime

class Task:
    def __init__(self, client):
        self.client = client

    def create_task(self, task_input: TaskCreate) -> TaskOut:
        """
        Create a new Task and send it to the GraphQL API.
        
        Args:
            task_input (TaskCreate): The input data for creating a new Task.
        
        Returns:
            TaskOut: The created Task.
        """
        variables = {
            "input": task_input.dict(exclude_none=True)
        }
        
        result = self.client.execute(CREATE_TASK, variable_values=variables)
        
        created_task = result['createTask']
        
        return TaskOut(
            id=created_task['id'],
            name=created_task['name'],
            description=created_task['description'],
            estimated_time_mins=created_task['estimated_time_mins'],
            priority=created_task['priority'],
            tags=created_task['tags'],
            createdAt=datetime.fromisoformat(created_task['createdAt'].replace('Z', '+00:00')),
            updatedAt=datetime.fromisoformat(created_task['updatedAt'].replace('Z', '+00:00'))
        )

    def list_tasks(self, nm: NullModel) -> List[TaskOut]:
        """
        List all Tasks from the GraphQL API.
        
        Returns:
            List[TaskOut]: A list of all Tasks.
        """
        result = self.client.execute(LIST_TASKS)
        
        tasks = result['listTasks']['items']
        return [
            TaskOut(
                id=task['id'],
                name=task['name'],
                description=task['description'],
                estimated_time_mins=task['estimated_time_mins'],
                priority=task['priority'],
                tags=task['tags'],
                createdAt=datetime.fromisoformat(task['createdAt'].replace('Z', '+00:00')),
                updatedAt=datetime.fromisoformat(task['updatedAt'].replace('Z', '+00:00'))
            ) for task in tasks
        ]

