import re
import json
import markdown2


def save_markdown_as_html(markdown_content: str):
    # Convert markdown to HTML
    html_content = markdown2.markdown(markdown_content, extras=[
                                      "tables", "fenced-code-blocks"])

    # Wrap it in a basic HTML structure to improve styling
    full_html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1, h2, h3, h4, h5, h6 {{ color: #333; }}
            pre {{ background-color: #f4f4f4; padding: 10px; border-radius: 5px; }}
            code {{ font-family: monospace; color: #d63384; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """

    # Save the HTML to a file
    return full_html


def extract_json_from_markdown(string: str) -> dict:

    pattern = r'```json\s*(.*?)\s*```'

    matches = re.finditer(pattern, string, re.DOTALL)

    matches_list = list(matches)

    if not matches_list:
        raise ValueError("No JSON code blocks found in the string")

    last_json_content = matches_list[-1].group(1).strip()

    return json.loads(last_json_content)
