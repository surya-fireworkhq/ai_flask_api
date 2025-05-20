import ollama
from flask import Flask, request, jsonify

# --- Copied from ollama_test.py ---
def generate_selenium_locator(html_data: str, user_prompt: str, model_name: str = "llama3.2:latest") -> str | None:
    """Generates a Selenium locator using an Ollama model based on HTML and a user prompt.

    Args:
        html_data: The HTML snippet or full HTML content.
        user_prompt: The user's description of the target element.
        model_name: The name of the Ollama model to use (e.g., "mistral", "codellama", "qwen-2.5-coder:7b").

    Returns:
        The generated Selenium locator string, or None if an error occurs or no locator is found.
    """
    system_message = """    You are an expert AI assistant specializing in web automation and Selenium.
    Your task is to analyze the provided HTML data and a user's description of a target web element.
    Based on this, you must generate the most robust and concise Selenium locator (preferably XPath or CSS Selector) for that element.
    Important: Do not explain and not include any other text or comments.

    Consider the following when generating the locator:
    1.  **IDs**: Prioritize using `id` attributes if they are present and likely unique.
    2.  **Names**: Use `name` attributes if `id` is not suitable.
    3.  **Specific Attributes**: Use other descriptive attributes like `class`, `data-*`, `aria-label`, etc.
    4.  **Text Content**: Use element text content, especially for buttons, links, and headers.
    5.  **Combination**: Combine attributes and text for more robust locators if necessary.
    6.  **Conciseness**: Prefer shorter, more direct locators over overly long and complex ones.
    7.  **Robustness**: Avoid locators that are highly dependent on the exact DOM structure (e.g., very deep, indexed-based XPaths) unless no other option exists.

    Respond ONLY with the Selenium locator string itself.
    For example:
    - `xpath=//button[@id='submit-button']`
    - `css=input[name='username']`
    - `xpath=//a[contains(text(),'Learn More')]`
    - `id=main-logo`
    """

    full_prompt = f"""    Here is the HTML data:
    ```html
    {html_data}
    ```

    Here is the user's description of the target element:
    "{user_prompt}"

    Generate the Selenium locator:
    """

    try:
        # Using a print statement for logging in a simple Flask app.
        # For production, use Flask's logger or a dedicated logging library.
        print(f"\n--- Sending request to Ollama model: {model_name} for prompt: {user_prompt[:50]}... ---")

        response = ollama.chat(
            model=model_name,
            messages=[
                {
                    'role': 'system',
                    'content': system_message,
                },
                {
                    'role': 'user',
                    'content': full_prompt,
                }
            ],
            # stream=False # Ensure you get the full response at once
        )

        generated_locator = response['message']['content'].strip()
        print(f"--- Ollama's Raw Response ---\n{generated_locator}")

        if not generated_locator or len(generated_locator.split('=')) < 2:
            print("Warning: The model's response doesn't look like a standard locator format.")
            # Optionally, you might want to still return the raw response or a specific error structure
            # For now, we return it as is, and the client can decide.

        return generated_locator

    except Exception as e:
        print(f"Error interacting with Ollama: {e}")
        return None
# --- End of copied function ---

app = Flask(__name__)

@app.route('/api/generate-locator', methods=['POST'])
def handle_generate_locator():
    """    API endpoint to generate a Selenium locator.
    Expects JSON payload:
    {
        "html_data": "...",
        "user_prompt": "...",
        "model_name": "optional_model_name" // e.g., "qwen2.5-coder:7b", defaults to "mistral"
    }
    """
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    html_data = data.get('html_data')
    user_prompt = data.get('user_prompt')
    # model_name = data.get('model_name', 'qwen2.5-coder:7b') # Default model if not provided
    model_name = data.get('model_name', 'llama3.2:latest') # Default model if not provided

    if not html_data or not user_prompt:
        return jsonify({"error": "Missing 'html_data' or 'user_prompt' in JSON payload"}), 400

    print(f"Received API request for model '{model_name}' with prompt: '{user_prompt}'")

    locator = generate_selenium_locator(html_data, user_prompt, model_name=model_name)

    if locator:
        locator = deserialize_locator_string(locator)
        return jsonify({"locator": locator}), 200
    else:
        # Consider if the model returned a non-standard format that was caught by the warning
        # For now, any None or problematic (but not error-raising) output from generate_selenium_locator
        # will lead to this "could not generate" error.
        return jsonify({"error": "Could not generate locator or an internal error occurred"}), 500



def deserialize_locator_string(locator_block: str) -> str:
    """
    Deserializes a locator string that might be wrapped in markdown code blocks
    (single or triple backticks) and may contain a language specifier.

    Args:
        locator_block: The string potentially containing the wrapped locator.

    Returns:
        The cleaned, unwrapped locator string.
    """
    content = locator_block.strip()

    if content.startswith("```") and content.endswith("```"):
        content = content[3:-3] # Remove triple backticks
        # Check if the first line is purely a language specifier (e.g., "xpath", "css")
        # and there's content on the next line.
        lines = content.split('\n', 1)
        if len(lines) > 1:
            first_line_candidate = lines[0].strip()
            # Simple heuristic: if the first line is short, purely alphabetic,
            # and the second line starts with a common locator pattern or contains '=',
            # it's likely a language specifier.
            if first_line_candidate.isalpha() and \
               not any(c in first_line_candidate for c in ['=', '[', '/', '.']) and \
               lines[1].strip() != "":
                # It's likely a language specifier line, so we take the rest
                content = lines[1]
        content = content.strip() # Strip again after potentially removing language line
    elif content.startswith("`") and content.endswith("`"):
        content = content[1:-1].strip() # Remove single backticks and strip

    return content


if __name__ == '__main__':
    # Note: For production, use a proper WSGI server like Gunicorn or uWSGI.
    # Example: gunicorn -w 4 -b 0.0.0.0:5001 app:app
    app.run(debug=True, host='0.0.0.0', port=5001) 