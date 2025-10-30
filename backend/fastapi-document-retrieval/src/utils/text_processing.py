from typing import Any, Dict
import json

def extract_fields_from_json(json_data: str, fields: Dict[str, str]) -> Dict[str, Any]:
    """
    Extract specified fields from a JSON string.

    Args:
        json_data (str): The JSON string to extract fields from.
        fields (Dict[str, str]): A dictionary where keys are the desired output field names
                                  and values are the corresponding keys in the JSON data.

    Returns:
        Dict[str, Any]: A dictionary containing the extracted fields.
    """
    data = json.loads(json_data)
    extracted_data = {output_field: data.get(input_field) for output_field, input_field in fields.items()}
    return extracted_data

def clean_text(text: str) -> str:
    """
    Clean the input text by removing unnecessary whitespace and special characters.

    Args:
        text (str): The text to clean.

    Returns:
        str: The cleaned text.
    """
    return ' '.join(text.split())  # Remove extra whitespace

def tokenize_text(text: str) -> list:
    """
    Tokenize the input text into words.

    Args:
        text (str): The text to tokenize.

    Returns:
        list: A list of tokens (words).
    """
    return text.split()  # Simple whitespace-based tokenization

def preprocess_text(text: str) -> str:
    """
    Preprocess the input text by cleaning and tokenizing.

    Args:
        text (str): The text to preprocess.

    Returns:
        str: The preprocessed text.
    """
    cleaned_text = clean_text(text)
    tokens = tokenize_text(cleaned_text)
    return ' '.join(tokens)  # Return the tokens as a single string
