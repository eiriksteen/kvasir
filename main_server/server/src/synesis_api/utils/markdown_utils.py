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


def convert_markdown_to_html(markdown_content: str):
    # Convert markdown to HTML
    html_content = markdown2.markdown(markdown_content, extras=[
                                      "tables", "fenced-code-blocks"])

    # Wrap it in a basic HTML structure to improve styling
    full_html = f"""
    <html>
    <head>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-tomorrow.min.css" rel="stylesheet" />
        <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-core.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/plugins/autoloader/prism-autoloader.min.js"></script>
        <style>
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; 
                margin: 20px; 
                line-height: 1.6;
                color: #333;
            }}
            h1, h2, h3, h4, h5, h6 {{ 
                color: #2c3e50; 
                margin-top: 1.5em;
                margin-bottom: 0.5em;
            }}
            h1 {{ font-size: 2.2em; border-bottom: 3px solid #3498db; padding-bottom: 0.3em; }}
            h2 {{ font-size: 1.8em; border-bottom: 2px solid #e74c3c; padding-bottom: 0.2em; }}
            h3 {{ font-size: 1.5em; color: #8e44ad; }}
            
            pre {{ 
                background-color: #2d3748; 
                padding: 1.2em; 
                border-radius: 8px; 
                margin: 1.5em 0;
                overflow-x: auto;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                border-left: 4px solid #3498db;
            }}
            
            code {{ 
                font-family: 'Fira Code', 'Monaco', 'Consolas', 'Liberation Mono', 'Courier New', monospace; 
                font-size: 0.9em;
                line-height: 1.4;
            }}
            
            pre code {{
                color: #e2e8f0;
                background: none;
                padding: 0;
                border-radius: 0;
                font-size: 0.9em;
            }}
            
            /* Python-specific syntax highlighting improvements */
            .token.keyword {{ color: #ff79c6; }}
            .token.string {{ color: #f1fa8c; }}
            .token.number {{ color: #bd93f9; }}
            .token.comment {{ color: #6272a4; font-style: italic; }}
            .token.function {{ color: #50fa7b; }}
            .token.class-name {{ color: #8be9fd; }}
            .token.operator {{ color: #ff79c6; }}
            
            table {{ 
                width: 100%; 
                border-collapse: collapse; 
                margin: 20px 0; 
                background: white;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }}
            th, td {{ 
                border: 1px solid #e2e8f0; 
                padding: 12px; 
                text-align: left; 
            }}
            th {{ 
                background-color: #f7fafc; 
                font-weight: 600;
                color: #2d3748;
            }}
            tr:nth-child(even) {{
                background-color: #f8fafc;
            }}
            
            /* Inline code styling */
            p code, li code {{
                background-color: #f1f5f9;
                color: #dc2626;
                padding: 0.2em 0.4em;
                border-radius: 4px;
                font-size: 0.85em;
                border: 1px solid #e2e8f0;
            }}
            
            /* Blockquote styling */
            blockquote {{
                border-left: 4px solid #3498db;
                margin: 1.5em 0;
                padding: 0.5em 1em;
                background-color: #f8fafc;
                border-radius: 0 8px 8px 0;
            }}
            
            /* List styling */
            ul, ol {{
                padding-left: 2em;
            }}
            
            li {{
                margin: 0.5em 0;
            }}
        </style>
    </head>
    <body>
        {html_content}
        <script>
            // Ensure Prism highlights all code blocks after content loads
            document.addEventListener('DOMContentLoaded', function() {{
                if (typeof Prism !== 'undefined') {{
                    Prism.highlightAll();
                }}
            }});
        </script>
    </body>
    </html>
    """

    # Save the HTML to a file
    return full_html
