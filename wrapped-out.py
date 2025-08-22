#Script to take a list of Postman collection API JSON and join its necessary env variables from another JSON file.
#The final script will generate a markdown output of the list, in-order for this work, the env variables must be unique in the list and not repeated.

#############
#By DeezSec##
#############

import json
import re

def get_environment_map(env_data):
    """
    Parses the Postman environment JSON data to create a key-value map.

    Args:
        env_data (dict): The loaded JSON data from the environment file.

    Returns:
        dict: A dictionary mapping variable keys to their values.
    """
    variable_map = {}
    if 'values' in env_data and isinstance(env_data['values'], list):
        for item in env_data['values']:
            if item.get('enabled', False) and 'key' in item and 'value' in item:
                variable_map[item['key']] = item['value']
    return variable_map

def find_and_process_items(collection_item, env_map):
    """
    Recursively traverses the Postman collection structure to find and
    resolve URLs and methods in API requests.

    Args:
        collection_item (dict or list): The current item/folder from the collection.
        env_map (dict): The dictionary of environment variables.

    Returns:
        list: A list of tuples, where each tuple contains the method and the
              fully resolved URL (e.g., [('GET', 'http://...')]).
    """
    resolved_requests = []

    # If the current item is a list (e.g., a folder's 'item' array)
    if isinstance(collection_item, list):
        for item in collection_item:
            resolved_requests.extend(find_and_process_items(item, env_map))
        return resolved_requests

    # If the item is a folder (contains an 'item' key)
    if 'item' in collection_item and isinstance(collection_item['item'], list):
        resolved_requests.extend(find_and_process_items(collection_item['item'], env_map))

    # If the item is an actual request (contains a 'request' key)
    if 'request' in collection_item:
        try:
            # Extract the raw URL string and the HTTP method
            raw_url = collection_item['request']['url']['raw']
            method = collection_item['request'].get('method', 'N/A') # Use .get for safety
            
            # Use regex to find all {{variable}} placeholders
            placeholders = re.findall(r"\{\{([^{}]+)\}\}", raw_url)
            
            # Replace each placeholder with its value from the environment map
            resolved_url = raw_url
            for placeholder in placeholders:
                if placeholder in env_map:
                    resolved_url = resolved_url.replace(f"{{{{{placeholder}}}}}", env_map[placeholder])
            
            # Append the method and resolved URL as a tuple
            resolved_requests.append((method, resolved_url))
        except (KeyError, TypeError):
            # Ignore items that don't have the expected structure
            pass
            
    return resolved_requests

def main():
    """
    Main function to run the script.
    """
    try:
        # Get file paths from the user and strip any surrounding quotes
        collection_file_path = input("Enter the path to the Postman collection JSON file: ").strip(' "')
        env_file_path = input("Enter the path to the Postman environment JSON file: ").strip(' "')

        # Read and load the collection JSON file
        with open(collection_file_path, 'r', encoding='utf-8') as f:
            collection_data = json.load(f)

        # Read and load the environment JSON file
        with open(env_file_path, 'r', encoding='utf-8') as f:
            env_data = json.load(f)

        # Create the environment variable map
        env_map = get_environment_map(env_data)

        if not env_map:
            print("\nWarning: No enabled variables found in the environment file.")
            return

        # Find and resolve all requests in the collection
        final_requests = find_and_process_items(collection_data.get('item', []), env_map)

        # Print the results in Markdown table format
        if final_requests:
            print("\n## Resolved API Endpoints\n")
            print("| S.No | Method | API URL |")
            print("|:----:|:-------|:--------|")
            for i, (method, url) in enumerate(final_requests, 1):
                print(f"| {i} | `{method}` | {url} |")
            print("\n")
        else:
            print("\nNo API requests with URLs were found in the collection.")

    except FileNotFoundError:
        print("\nError: One of the files was not found. Please check the paths and try again.")
    except json.JSONDecodeError:
        print("\nError: Failed to decode JSON. Please ensure both files are valid JSON.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")

if __name__ == "__main__":

    main()
