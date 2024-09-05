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
    scheduled_date_utc
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
      scheduled_date_utc
      createdAt
      updatedAt
    }
  }
}
""")

DELETE_TASK = gql("""
mutation DeleteTask($input: DeleteTaskInput!) {
  deleteTask(input: $input) {
    id
    name
    description
    estimated_time_mins
    priority
    tags
    scheduled_date_utc
    createdAt
    updatedAt
  }
}
""")

UPDATE_TASK = gql("""
mutation UpdateTask($input: UpdateTaskInput!) {
  updateTask(input: $input) {
    id
    name
    description
    estimated_time_mins
    priority
    tags
    scheduled_date_utc
    createdAt
    updatedAt
  }
}
""")


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
            scheduled_date_utc=created_task['scheduled_date_utc'],
            createdAt=datetime.fromisoformat(created_task['createdAt'].replace('Z', '+00:00')),
            updatedAt=datetime.fromisoformat(created_task['updatedAt'].replace('Z', '+00:00'))
        )

    def list_tasks(self, nm: NullModel) -> TaskList:
        """
        List all Tasks from the GraphQL API.

        Returns:
            TaskList: A list of all Tasks wrapped in a TaskList object.
        """
        result = self.client.execute(LIST_TASKS)

        tasks = result['listTasks']['items']
        task_list = [
            TaskOut(
                id=task['id'],
                name=task['name'],
                description=task['description'],
                estimated_time_mins=task['estimated_time_mins'],
                priority=task['priority'],
                tags=task['tags'],
                scheduled_date_utc=task['scheduled_date_utc'],
                createdAt=datetime.fromisoformat(task['createdAt'].replace('Z', '+00:00')),
                updatedAt=datetime.fromisoformat(task['updatedAt'].replace('Z', '+00:00'))
            ) for task in tasks
        ]
        return TaskList(tasks=task_list)

    def delete_task(self, task_id: TaskId) -> TaskOut:
        """
        Delete a Task from the GraphQL API.

        Args:
            task_id (TaskId): The ID of the task to delete.

        Returns:
            TaskOut: The deleted Task.
        """
        variables = {
            "input": {
                "id": task_id.id
            }
        }

        result = self.client.execute(DELETE_TASK, variable_values=variables)

        deleted_task = result['deleteTask']

        return TaskOut(
            id=deleted_task['id'],
            name=deleted_task['name'],
            description=deleted_task['description'],
            estimated_time_mins=deleted_task['estimated_time_mins'],
            priority=deleted_task['priority'],
            tags=deleted_task['tags'],
            scheduled_date_utc=deleted_task['scheduled_date_utc'],
            createdAt=datetime.fromisoformat(deleted_task['createdAt'].replace('Z', '+00:00')),
            updatedAt=datetime.fromisoformat(deleted_task['updatedAt'].replace('Z', '+00:00'))
        )

    def update_task(self, update_input: UpdateTaskInput) -> TaskOut:
        """
        Update a Task in the GraphQL API.

        Args:
            update_input (UpdateTaskInput): The input data for updating the task.

        Returns:
            TaskOut: The updated Task.
        """
        variables = {
            "input": update_input.dict(exclude_none=True)
        }

        result = self.client.execute(UPDATE_TASK, variable_values=variables)

        updated_task = result['updateTask']

        return TaskOut(
            id=updated_task['id'],
            name=updated_task['name'],
            description=updated_task['description'],
            estimated_time_mins=updated_task['estimated_time_mins'],
            priority=updated_task['priority'],
            tags=updated_task['tags'],
            scheduled_date_utc=updated_task['scheduled_date_utc'],
            createdAt=datetime.fromisoformat(updated_task['createdAt'].replace('Z', '+00:00')),
            updatedAt=datetime.fromisoformat(updated_task['updatedAt'].replace('Z', '+00:00'))
        )
