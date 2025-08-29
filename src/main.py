import os
import json
from openai import OpenAI
import re
import llm_api

MODEL = "gpt-4.1"
CLIENT = OpenAI()

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))    # /src
BASE_DIR = os.path.dirname(CURRENT_DIR)                     # /
# PROMPT_DIR = BASE_DIR + "/prompt/ja/"
PROMPT_DIR = BASE_DIR + "/prompt/en/"

def txt_reader(filepath: str) -> str:
    """
    Reads the content of a text file.
    Args:
        filepath (str): The path to the text file.
    Returns:
        str: The content of the file.
    """
    f = open(filepath, 'r')
    return f.read()

def json_reader(filepath: str) -> dict:
    """
    Reads the content of a JSON file and returns a dictionary.
    Args:
        filepath (str): The path to the JSON file.
    Returns:
        dict: The content of the JSON file as a dictionary.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)
    
def extract_code_snippet(llm_response_content: str) -> str:
    """
    Extracts a code snippet from the LLM's response,
    assuming it's formatted as a Markdown code block.
    Args:
        llm_response_content (str): The full content of the LLM's response.
    Returns:
        str: The extracted code snippet, or the original content if no code block is found.
    """
    match = re.search(r"```(?:\w+)?\n(.*?)```", llm_response_content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return llm_response_content

def modify_spell(inspected_model: str) -> tuple[str, dict, str]:
    """
    Interacts with the LLM to correct spelling mistakes in the LTS/FLTL model.
    Args:
        inspected_model (str): The current LTS/FLTL model to be inspected.
    Returns:
        tuple[str, dict, str]: The prompt sent to LLM, the LLM's full response dictionary,
                                and the extracted modified model string (suggestion).
    """
    
    prompt_template_json = json_reader(PROMPT_DIR + 'spell_prompt_data.json')
    prompt_data_for_llm = prompt_template_json.copy()
    json_string_for_llm = json.dumps(prompt_data_for_llm, indent=2, ensure_ascii=False)    
    
    prompt_context = (
        json_string_for_llm +
        "\n\nHere is the model to be checked for spelling errors:\n\n" +
        inspected_model
    )
    system_message = (
        "You are a **compile checker** specialized in correcting spelling mistakes "
        "in LTS and FLTL models for Discrete Controller Synthesis (DCS). "
        "Given a model description (which will follow the JSON-formatted prompt), " # 指示を更新
        "detect spelling mistakes (excluding grammatical errors) and suggest corrections.\n\n"
        "**【CRUCIAL OUTPUT FORMAT RULE: SPELLING CORRECTION】**\n"
        "- **If no spelling mistakes are found (or compilation is deemed successful by you):** "
        "Respond with \"No spelling mistakes found. Compilation expected to be successful.\" "
        "and **immediately thereafter, provide the entire model in a single Markdown code block (```plaintext). No other explanations are needed.**\n"
        "- **If spelling mistakes are detected:**\n"
        "  - First, **provide the entire corrected model as a single Markdown code block (```plaintext). This is the highest priority.**\n"
        "  - **Immediately after** the code block, briefly explain **the errors that needed correction and their reasons** in a bulleted list.\n"
        "  - Even if there are multiple errors, the **initial code block must contain the complete model after applying all corrections**."
    )
    prompt, response = llm_api.chat(
        CLIENT,
        MODEL,
        prompt_context, 
        True, # Use initial history (start a new session)
        system_message
    )
    suggested_model = extract_code_snippet(response['content']) # Renamed to suggested_model for clarity
    return prompt, response, suggested_model

def modify_grammer(inspected_model: str, error_statement: str) -> tuple[str, dict, str]:
    """
    Interacts with the LLM to correct grammatical mistakes in the LTS/FLTL model.
    Args:
        inspected_model (str): The current LTS/FLTL model to be inspected.
        error_statement (str): The compilation error message from the user.
    Returns:
        tuple[str, dict, str]: The prompt sent to LLM, the LLM's full response dictionary,
                                and the extracted modified model string (suggestion).
    """
    
    prompt_data_for_llm = json_reader(PROMPT_DIR + 'grammer_prompt_data.json')

    if "current_correction_context" not in prompt_data_for_llm:
        prompt_data_for_llm["current_correction_context"] = {}
    
    error_instruction_with_id_prompt = (
        "The compiler provides the line number where it encountered an issue and explains the nature of the error. "
        "Please use this error message, along with the provided grammatical syntax error examples, to identify and correct the error in the model. "
        "**For each correction, please indicate the ID of the grammatical example (from the 'grammar_correction_examples' list) that you referred to, if applicable.**"
    )
    prompt_data_for_llm["current_correction_context"]["error_instruction"] = error_instruction_with_id_prompt
    prompt_data_for_llm["current_correction_context"]["compilation_error_message"] = error_statement
    prompt_data_for_llm["current_correction_context"]["model_to_correct"] = inspected_model

    
    json_string_for_llm = json.dumps(prompt_data_for_llm, indent=2, ensure_ascii=False)
    prompt_content = json_string_for_llm
    
    system_message = (
        "You are an **interactive compile checker** specialized in correcting grammatical mistakes "
        "in LTS and FLTL models for Discrete Controller Synthesis (DCS). "
        "Given a JSON-formatted prompt containing model description and compilation error message, "
        "detect grammatical errors and suggest corrections. "
        "This process will repeat until compilation is fully successful.\n\n"
        "**【CRUCIAL OUTPUT FORMAT RULE: GRAMMAR CORRECTION】**\n"
        "- **If no grammatical mistakes are found (or compilation is deemed successful by you):** "
        "Respond with \"No grammatical mistakes found. Compilation completed successfully.\" "
        "and **immediately thereafter, provide the entire corrected model as a single Markdown code block (```plaintext). No other explanations are needed.**\n"
        "- **If grammatical mistakes are detected:**\n"
        "  - First, **provide the entire corrected model as a single Markdown code block (```plaintext). This is the highest priority.**\n"
        "  - **Immediately after** the code block, briefly explain **the errors that needed correction, their reasons, AND THE ID(S) OF THE GRAMMAR EXAMPLE(S) AND GRAMMAR RULE(S) THAT YOU REFERRED TO (e.g., 'Referenced Grammar Example ID: 5, Referenced Grammar Rule ID: LTS_3').** If multiple examples/rules apply, list all relevant IDs. If no specific example/rule was directly referenced, state 'No specific reference'. Use a bulleted list for each error.\n"
        "  - If there are multiple errors, list all errors and provide corrections for each."
    )
    prompt, response = llm_api.chat(
        CLIENT,
        MODEL,
        prompt_content, 
        True, 
        system_message
    )
    suggested_model = extract_code_snippet(response['content'])
    return prompt, response, suggested_model


current_model_path = BASE_DIR + '/input/input_model.txt'
inspected_model = txt_reader(current_model_path)

# Modify Spell
print("--- Starting Spelling Correction Phase ---")
prompt_spell, response_spell, inspected_model = modify_spell(inspected_model)

print("\n--- LLM's Spelling Correction Result ---")
print(f"Prompt sent to LLM:\n{prompt_spell}")
print(f"LLM's response:\n{response_spell['content']}")
print(f"\nCorrected model after spell check (extracted):\n{inspected_model}")

while True:
    write_confirm = input(
        f"Please update the spelling in {current_model_path} based on the suggestion above. "
        "Have you finished modifying the file? (Y): "
    ).upper()
    if write_confirm == 'Y':
        inspected_model = txt_reader(current_model_path)
        print(f"{current_model_path} has been reloaded with the latest model.")
        break
    else:
        print("Please modify the file and enter 'Y' to continue.")

# Modify Grammer
print("\n--- Starting Grammar Correction Phase ---")
while True:
    user_feedback = input("Have you compiled the model above? Did compilation pass? (Y/n): ").upper()
    if user_feedback == 'Y':
        print("Syntax errors have been successfully corrected!")
        break
    elif user_feedback == 'N':
        compilation_error = input("Please paste the compilation error message: ")
        prompt_grammer, response_grammer, suggested_grammer_model = modify_grammer(inspected_model, compilation_error)

        # Display LLM's grammar correction suggestion
        print("\n--- LLM's Grammar Correction Suggestion ---")
        print(f"Prompt sent to LLM:\n{prompt_grammer}")
        print(f"LLM's full response:\n{response_grammer['content']}") # Display full LLM response
        print(f"\n【LLM's Suggested Model】\n{suggested_grammer_model}") # Display extracted suggested model

        
        while True:
            write_confirm = input(
                f"Please update the grammar in {current_model_path} based on the suggestion above. "
                "Have you finished modifying the file? (Y): "
            ).upper()
            if write_confirm == 'Y':
                inspected_model = txt_reader(BASE_DIR + '/input/input_model.txt')
                print(f"{current_model_path} has been reloaded with the latest model.")
                break
            else:
                print("Input Y")
                
        print(f"\nNext suggested corrected model (extracted):\n{inspected_model}")
    else:
        print("Invalid input. Please enter 'Y' or 'n'.")

print("\n--- Final Model ---")
print(inspected_model)
