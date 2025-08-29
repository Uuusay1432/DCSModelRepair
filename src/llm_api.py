import json
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))    # /src
RECORD_PATH = CURRENT_DIR + "/../log/record.txt"            # /log/record.txt
LOG_PATH = CURRENT_DIR + "/../log/log.txt"                  # /log/log.txt 

def load_chat_history():
    """
    Load past conversations from the chat history file.
    If the file does not exist or is invalid JSON, no error occurs; an empty list is returned.
    """
    if not os.path.exists(RECORD_PATH):
        return []
    
    with open(RECORD_PATH, 'rb') as f:
        temp = f.read()
        try:
            historic_messages = json.loads(temp)
        except json.JSONDecodeError:
            print(f"Warning: Could not decode JSON from {RECORD_PATH}. Returning empty history.")
            return []
    return historic_messages

def save_chat_history(messages: list):
    """
    Saved the updated chat history to RECORD_PATH.
    """
    try:
        with open(RECORD_PATH, "wb") as f:
            f.write(json.dumps(messages, indent=4, ensure_ascii=False).encode('utf-8'))
    except IOError as e:
        print(f"Error saving chat history to {RECORD_PATH}: {e}")

def log_message(message: dict):
    """
    Record any messages (from users, assistants, systems, etc.) to LOG_PATH.
    """
    try:
        with open(LOG_PATH, "a", encoding='utf-8') as f:
            f.write(json.dumps(message, indent=4, ensure_ascii=False) + ",\n")
    except IOError as e:
        print(f"Error logging message to {LOG_PATH}: {e}")

def create_message_dict(role: str, content: str):
    """
    Create a message dictionary based on role and content.
    Args:
        role (str): ‘user’, ‘assistant’, or ‘system’
        content (str): Message content
    Returns:
        dict: Formatted message dictionary
    Raises:
        ValueError: If an invalid role is specified
    """
    if role not in ['user', 'assistant', 'system']:
        raise ValueError("Invalid role. Must be 'user', 'assistant', or 'system'.")
    return {"role": role, "content": content}

def call_llm_api(client, model: str, messages: list):
    """
    Call the LLM API and retrieve the response.
    Args:
        client: The LLM API client object.
        model (str): The name of the LLM model to use.
        messages (list): A list of messages to send to the LLM.
    Returns:
        str: The response text from the LLM.
    Raises:
        Exception: If an error occurs during the API call.
    """
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=messages
        )
        response_content = completion.choices[0].message.content
        return response_content
    except Exception as e:
        print(f"Error calling LLM API: {e}")
        raise
    
def initialize_chat_history(initial_messages: list = None):
    """
    Resets the chat history and overwrites the RECORD_PATH with the specified initial message.
    If no initial message is specified, initializes with an empty history.
    Args:
        initial_messages (list, optional): List of initial messages to write to the history.
                                           Default is None (initializes with an empty list).
    """
    if initial_messages is None:
        initial_messages = []
    
    if not isinstance(initial_messages, list) or \
       not all(isinstance(msg, dict) and 'role' in msg and 'content' in msg for msg in initial_messages):
        raise ValueError("initial_messages must be a list of dictionaries with 'role' and 'content' keys.")
        
    save_chat_history(initial_messages)
    print(f"Chat history initialized with {len(initial_messages)} messages.")

def get_initial_chat_history(system_message: str = None):
    """
    Retrieves the initial chat history (typically system messages) when starting a chat.
    Unlike load_chat_history, which loads existing history,
    this is intended for use when starting a new chat session each time.
    Args:
        system_message (str, optional): System messages defining chat behavior.
                                        If specified, added as the first element of the history.
    Returns:
        list: List of initial chat history.
    """
    initial_history = []
    if system_message:
        initial_history.append(create_message_dict('system', system_message))
    return initial_history


def chat(client, model: str, prompt: str, use_initial_history: bool = False, system_message: str = None):
    """
    Interact with LLM while considering chat history.
    Load existing history or generate and use initial history, add prompts, invoke LLM,
    save responses to history, and log them.
    Args:
        client: LLM API client object.
        model (str): Name of the LLM model to use.
        prompt (str): New prompt from the user.
        use_initial_history (bool): If True, do not load existing history;
                                    use initial history (including system_message if present) as a new session.
                                    If False, load history from existing RECORD_PATH.
        system_message (str, optional): When use_initial_history=True,
                                        a string to add as a system message at the start of the chat.
    Returns:
        tuple: (user_prompt_dict, LLM_response_dict)
    """
    if use_initial_history:
        current_messages = get_initial_chat_history(system_message=system_message)
    else:
        current_messages = load_chat_history()

    user_message_dict = create_message_dict('user', prompt)
    log_message(user_message_dict)

    current_messages.append(user_message_dict)

    try:
        llm_response_content = call_llm_api(client, model, current_messages)
    except Exception as e:
        print(f"Chat failed: {e}")
        assistant_error_message = "we were unable to process your request at this time."
        assistant_message_dict = create_message_dict('assistant', assistant_error_message)
        
        log_message(assistant_message_dict)

        current_messages.append(assistant_message_dict)
        save_chat_history(current_messages) 
        
        return user_message_dict, assistant_message_dict

    assistant_message_dict = create_message_dict('assistant', llm_response_content)
    current_messages.append(assistant_message_dict)

    save_chat_history(current_messages)

    log_message(assistant_message_dict)

    return user_message_dict, assistant_message_dict
