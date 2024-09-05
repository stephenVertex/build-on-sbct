from time import time
from typing import Dict, List, Any, Optional, Tuple, Union
from typing_extensions import Annotated
from pydantic import BaseModel, Field, ValidationError

################################################################################
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich.text import Text
from rich.style import Style
from rich.theme import Theme

################################################################################

import json
import boto3
import requests
from datetime import datetime, timedelta
import pytz
import dateparser
import os
import uuid
import pickle
import yaml
import copy
import base64


from PydanticTaskModels import *

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown


from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit import prompt
from prompt_toolkit.keys import Keys
from prompt_toolkit.filters import Condition
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import ANSI, HTML
from prompt_toolkit.styles import Style

################################################################################
##
def get_current_datetime(NullModel) -> CurrentDateTime:
    return CurrentDateTime(current_datetime=datetime.now(pytz.timezone('US/Pacific')))

def plaintext_datetime_to_millis(pt: InputDatetimePlaintext) -> DatetimeMillis:
    parsed_start_date = dateparser.parse(pt.input_dt)
    if parsed_start_date:
        return DatetimeMillis(datetime_millis=str(int(parsed_start_date.timestamp() * 1000)))
    return None


def plaintext_datetime_to_seconds(pt: InputDatetimePlaintext) -> DatetimeSeconds:
    parsed_start_date = dateparser.parse(pt.input_dt)
    if parsed_start_date:
        return DatetimeSeconds(datetime_seconds=str(int(parsed_start_date.timestamp())))
    return None




################################################################################
## The models we made
from TaskAccess import *
from TodoAccess import *
from OKRAccess  import *

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


################################################################################
## Creating a set of tool schemas so I can use it for an agent

function_io_map = {
    "get_current_datetime": {
        "input": NullModel,
        "output": CurrentDateTime,
        "description": "Returns the current date and time in the US Pacific Time Zone.",
        "function": get_current_datetime
    },
    "list_okrs" : {
        "input" : NullModel,
        "output" : OKROutList,
        "description" : "Lists all current OKRs",
        "function" : okr_client.list_okrs
    },
    "plaintext_datetime_to_millis": {
        "input": InputDatetimePlaintext,
        "output": DatetimeMillis,
        "description": "Converts a human-readable date/time string to milliseconds since epoch. Useful for ClickUp API interactions.",
        "function": plaintext_datetime_to_millis
    },
    "plaintext_datetime_to_seconds": {
        "input": InputDatetimePlaintext,
        "output": DatetimeSeconds,
        "description": "Converts a human-readable date/time string to milliseconds since epoch. Useful for ClickUp API interactions.",
        "function": plaintext_datetime_to_seconds
    },        
    "create_task": {
        "input": TaskCreate,
        "output": TaskOut,
        "description": "Creates a new Task and sends it to the GraphQL API.",
        "function": task_client.create_task
    },
    "list_tasks": {
        "input": NullModel,
        "output": TaskList,
        "description": "Lists all Tasks from the GraphQL API.",
        "function": task_client.list_tasks
    },
    "delete_task": {
        "input": TaskId,
        "output": TaskOut,
        "description": "Deletes a Task from the GraphQL API.",
        "function": task_client.delete_task
    },
    "update_task": {
        "input": UpdateTaskInput,
        "output": TaskOut,
        "description": "Updates an existing Task in the GraphQL API.",
        "function": task_client.update_task
    },
}



def pydantic_to_json_schema(model: BaseModel) -> Dict[str, Any]:
    schema = model.schema()
    # Remove Pydantic-specific keys
    for key in ['title', 'description']:
        schema.pop(key, None)
    return schema

# Now, let's create the array of tools
tools = []

for func_name, func_info in function_io_map.items():
    input_type = func_info['input']
    output_type = func_info['output']
    description = func_info['description']
    
    tool = {
        "name": func_name,
        "description": description,
        "inputSchema": { "json" : pydantic_to_json_schema(input_type) }
    }
    
    tools.append({"toolSpec" : tool})

# Print the resulting tools array
# print("--------------------------------------------------------------------------------")
# print("The tools array")
# print(json.dumps(tools, indent=2))
# print("--------------------------------------------------------------------------------")

def process_tool_call(tool_name, tool_input):
    if tool_name not in function_io_map:
        raise ValueError(f"Unknown tool: {tool_name}")

    func_info = function_io_map[tool_name]
    input_model = func_info['input']
    output_model = func_info['output']
    function = func_info['function']

    try:
        # Validate and create input object
        validated_input = input_model(**tool_input)
    except ValidationError as e:
        return {"error": f"Invalid input: {str(e)}"}

    # Call the function directly using the reference from function_io_map
    result = function(validated_input)

    # Check if the result is of the expected output type
    #if not isinstance(result, output_model):
    #    return {"error": f"Function returned unexpected type. Expected {output_model.__name__}, got {type(result).__name__}"}

    return result

################################################################################
## Converse API

client = boto3.client(
    service_name='bedrock-runtime',
    region_name='us-east-1'  # e.g., 'us-east-1'
)
MODEL_NAME= "anthropic.claude-3-5-sonnet-20240620-v1:0"

console = Console()

def print_function_io_map(function_io_map):
    console = Console()
    table = Table(title="Function I/O Map", show_header=True, header_style="bold magenta")
    table.add_column("Function Name", style="cyan", no_wrap=True)
    table.add_column("Input Type", style="green")
    table.add_column("Output Type", style="yellow")
    table.add_column("Description", style="blue")

    for func_name, func_info in function_io_map.items():
        table.add_row(
            func_name,
            func_info['input'].__name__,
            func_info['output'].__name__,
            Text(func_info['description'], style="italic")
        )

    console.print(Panel(table, expand=False, border_style="red"))

def handle_response_list(response_content, conversation_history, debug=False):
    """
    Print out the response, processing a tool call and adding it to the history if necessary.

    TODO Fix - this needs to be a list.
    It needs to build up a user response for each tool_use_block
    """
    used_tools_flag = False
    tool_use_element = {
        "role" : "user",
        "content" : []
    }

    for r0 in response_content:
        # console.print(Panel(json.dumps(r0, indent=2), title="r0", expand=False))

        # Handle TextBlock and ToolUseBlock specially
        if 'text' in r0.keys():
            console.print(Panel(Markdown(str(r0['text'])), title="Agent response", expand=False))
        elif 'toolUse' in r0.keys():
            used_tools_flag = True
            tool_use_id = r0['toolUse']['toolUseId']
            tool_name  = r0['toolUse']['name']
            tool_input = r0['toolUse']['input']
            if debug:
                console.print(f"\n[bold magenta]Tool Used:[/bold magenta] {tool_name}")
                console.print(Panel(json.dumps(tool_input, indent=2), title="Tool Input", expand=False))
                console.print(f"\n[bold magenta]...calling tool [/bold magenta] {tool_name}")

            tool_result = process_tool_call(tool_name, tool_input)
            if debug:
                console.print("Trying to dump tool_result")
                console.print(Panel(json.dumps(tool_result, indent=2), title="Tool Result", expand=False))

            # Add the assistant's response and tool use to the conversation history
            tool_use_element['content'].append(
                {
                    "toolResult" : {
                        "toolUseId": tool_use_id,
                        "content": [{"json" : json.loads(tool_result.json())}]
                    }
                }
            )

        else: ## Block type that we do not understand
            console.print(f"\n[bold orange]Different block type")
            console.print(Panel(str(r0)))

    if used_tools_flag:
        conversation_history.append(tool_use_element)

    return conversation_history
    

def chatbot_interaction(user_message, conversation_history, debug=False):

    console.print(Panel(f"[bold blue]User Message:[/bold blue] {user_message}", expand=False))
    
    # Add the new user message to the conversation history and ask the question
    conversation_history.append(user_message)

    response = client.converse(
        modelId=MODEL_NAME,
        inferenceConfig={"maxTokens" : 4096 }, 
        toolConfig={ "tools" : tools},
        messages=conversation_history
    )
    
    console.print("\n[bold green]Initial Response:[/bold green]")
    # console.print(str(response))
    # resp_type_list = [str(type(x)) for x in response['output']['message']['content']]
    # console.print(f"\n[bold green]{str(resp_type_list)}[/bold green]")

    # console.print(Panel(Markdown(str(response.content)), title="Content", expand=False))
    conversation_history.append({"role": "assistant", "content": response['output']['message']['content']})

    if debug:
        console.print(f"[yellow]Stop Reason:[/yellow] {response['stopReason']}")

    if response['stopReason'] == 'tool_use':
        while response['stopReason'] == 'tool_use':

            conversation_history = handle_response_list(response['output']['message']['content'], conversation_history, debug=debug)

            
            # console.print("Into R2: ")
            # console.print(str(conversation_history))
            ## We we are using a tool, we need to follow up.
            response2 = client.converse(
                modelId=MODEL_NAME,
                inferenceConfig={"maxTokens" : 4096 }, 
                toolConfig={ "tools" : tools},
                messages=conversation_history

            )
            console.print("\n[bold green]Tool Follow-up Response:[/bold green]")
            console.print(f"[yellow]Stop Reason:[/yellow] {response2['stopReason']}")

            # Add the final assistant's response to the conversation history
            conversation_history.append({"role": "assistant", "content": response2['output']['message']['content']})
            
            # Keep iterating while we have tools
            response = response2

        ## Finally, once I have excited the while loop, inject the last thing into the history
        conversation_history = handle_response_list(response['output']['message']['content'], conversation_history, debug=debug)
        
    else: ## For some other stop reason. This handles that we haven't even gone into the tool_use
          ## while loop
        console.print(f"[yellow]Stop Reason (else):[/yellow] {response['stopReason']}")
        # console.print(Panel(Markdown(str(response.content)), title="Content", expand=False))
        conversation_history = handle_response_list(response['output']['message']['content'], conversation_history, debug=debug)
            
    return None , conversation_history

def prompt_continuation(width, line_number, wrap_count):
    """
    The continuation: display line numbers and '->' before soft wraps.

    Notice that we can return any kind of formatted text from here.

    The prompt continuation doesn't have to be the same width as the prompt
    which is displayed before the first line, but in this example we choose to
    align them. The `width` input that we receive here represents the width of
    the prompt.
    """
    if wrap_count > 0:
        return " " * (width - 3) + "-> "
    else:
        text = ("- %i - " % (line_number + 1)).rjust(width)
        return HTML("<strong>%s</strong>") % text

def prompt_continuation_dots(width, line_number, is_soft_wrap):
    return '.' * width
    # Or: return [('', '.' * width)]


def multiline_input(prompt_text):
    console.print(prompt_text)
    answer = prompt(
        "Multiline input: ", multiline=True, prompt_continuation=prompt_continuation_dots
    )
    return answer

################################################################################
## Read file as document

def read_file_as_document(file_path):
    """
    Read a file and return a document object suitable for the model.
    """
    if not os.path.exists(file_path):
        return None, f"File not found: {file_path}"

    file_name = os.path.basename(file_path)
    _, file_extension = os.path.splitext(file_name)
    file_extension = file_extension.lower()

    format_mapping = {
        '.pdf': 'pdf',
        '.txt': 'txt',
        '.md': 'md',
        '.html': 'html'
    }

    if file_extension not in format_mapping:
        return None, f"Unsupported file format: {file_extension}"

    format = format_mapping[file_extension]

    with open(file_path, 'rb') as file:
        file_content = file.read()
        encoded_content = base64.b64encode(file_content).decode('utf-8')

    document = {
        "name": file_name,
        "format": format,
        "source": {"bytes": encoded_content}
    }

    return document, None

################################################################################
## SESSION LOGIC

def generate_session_id():
    return str(uuid.uuid4())


def ensure_saved_sessions_folder():
    if not os.path.exists("saved_sessions"):
        os.makedirs("saved_sessions")

def load_sessions():
    ensure_saved_sessions_folder()
    sessions = {}
    for filename in os.listdir("saved_sessions"):
        if filename.endswith(".pickle") and filename.startswith("session_"):
            session_id = filename[8:-7]  # Remove "session_" prefix and ".pickle" suffix
            with open(os.path.join("saved_sessions", filename), "rb") as f:
                session_data = pickle.load(f)
            sessions[session_id] = session_data
    return sessions

def save_session(session_id, conversation_history):
    ensure_saved_sessions_folder()
    filename = os.path.join("saved_sessions", f"session_{session_id}.pickle")
    session_data = {
        "session_id": session_id,
        "conversation_history": conversation_history,
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(filename, "wb") as f:
        pickle.dump(session_data, f)
    console.print(f"[bold green]Session saved: {session_id}[/bold green]")


def choose_session(sessions):
    console.print("[bold cyan]Available sessions:[/bold cyan]")
    for i, (session_id, session_data) in enumerate(sessions.items(), 1):
        console.print(f"{i}. Session {session_id[:8]}... (Last updated: {session_data.get('last_updated', 'Unknown')})")
    
    while True:
        try:
            choice = int(input("Enter the number of your choice (or 0 to start a new session): "))
            if choice == 0:
                return None  # Indicate that a new session should be created
            elif 1 <= choice <= len(sessions):
                return list(sessions.keys())[choice - 1]
            else:
                console.print("[bold red]Invalid choice. Please try again.[/bold red]")
        except ValueError:
            console.print("[bold red]Please enter a number.[/bold red]")

def main():
    console.print("[bold cyan]Welcome to the Task Management System![/bold cyan]")

    sessions = load_sessions()
    
    if sessions:
        console.print("[bold yellow]Do you want to load an existing session or create a new one?[/bold yellow]")
        console.print("1. Load an existing session")
        console.print("2. Create a new session")
        
        while True:
            choice = input("Enter your choice (1 or 2): ")
            if choice == "1":
                session_id = choose_session(sessions)
                if session_id is None:
                    session_id = generate_session_id()
                    conversation_history = []
                    console.print(f"[bold green]Created new session: {session_id}[/bold green]")
                else:
                    conversation_history = sessions[session_id]["conversation_history"]
                    console.print(f"[bold green]Loaded existing session: {session_id}[/bold green]")
                break
            elif choice == "2":
                session_id = generate_session_id()
                conversation_history = []
                console.print(f"[bold green]Created new session: {session_id}[/bold green]")
                break
            else:
                console.print("[bold red]Invalid choice. Please enter 1 or 2.[/bold red]")
    else:
        console.print("[bold yellow]No existing sessions found. Creating a new session.[/bold yellow]")
        session_id = generate_session_id()
        conversation_history = []
        console.print(f"[bold green]Created new session: {session_id}[/bold green]")

    console.print(f"[bold blue]Tools:[/bold blue]")
    for k,v in function_io_map.items():
        console.print(f"\t[blue]{k}[/blue]: {v['description']}")        

    should_i_clear_session = False
    document_to_send = None
    while True:
        user_input = multiline_input(f"\n(CH.len = {len(conversation_history)}: What would you like to do? (Type 'exit' to quit): ")
        
        if user_input.lower() == 'exit':
            console.print("[bold cyan]Thank you for using the Task Management System. Goodbye![/bold cyan]")
            save_session(session_id, conversation_history)
            break
        
        if user_input.lower() == '/s':
            console.print("[bold cyan]Summarizing session state and updating the history![/bold cyan]")
            user_input = "If I am in the state where I am planning social media posts, please generate a table of what I am working on and a list of the tasks created so far. Otherwise, write a summary of what I have been doing in this session. I am about to clear the contents."
            should_i_clear_session = True


        if user_input.startswith("/f "):
            file_path = user_input[3:].strip()
            document, error = read_file_as_document(file_path)
            if error:
                console.print(f"[bold red]{error}[/bold red]")
            else:
                document_to_send = document
                console.print(f"[bold green]File loaded: {document['name']}[/bold green]")
            continue


        if not user_input:
            console.print("[bold red]Empty input. Please type a message or 'exit' to quit.[/bold red]")
            continue

        message_content = [{"text": user_input}]
        if document_to_send:
            message_content.append({"document": document_to_send})
            document_to_send = None  # Reset after sending

        message = {"role": "user", "content": message_content}

        # cconsole.print(Panel(str(message), title="Message to API", expand=False))
        _ , conversation_history = chatbot_interaction(message, conversation_history)
        if should_i_clear_session:
            conversation_history = conversation_history[-2:]
            should_i_clear_session = False
            

        # Save the session after each interaction
        save_session(session_id, conversation_history)



if __name__ == "__main__":
    main()

