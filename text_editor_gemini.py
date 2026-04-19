import os
import json
import shutil
from typing import Optional, List
from dotenv import load_dotenv
from anthropic import Anthropic

# 1. Configuration & Client Setup
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = "https://openrouter.ai/api"
MODEL_NAME = "google/gemini-2.0-flash-001" # Updated to a stable Gemini 2.0 version

client = Anthropic(
    base_url=BASE_URL,
    api_key=OPENROUTER_API_KEY
)

# 2. The Core Logic Class
class TextEditorTool:
    def __init__(self, base_dir: str = ""):
        self.base_dir = base_dir or os.getcwd()
        self.backup_dir = os.path.join(self.base_dir, ".backups")
        os.makedirs(self.backup_dir, exist_ok=True)

    def _validate_path(self, file_path: str) -> str:
        abs_path = os.path.normpath(os.path.join(self.base_dir, file_path))
        if not abs_path.startswith(self.base_dir):
            raise ValueError(f"Access denied: {file_path} is outside allowed directory")
        return abs_path

    def view(self, path: str, view_range: Optional[List[int]] = None) -> str:
        abs_path = self._validate_path(path)
        if os.path.isdir(abs_path):
            return "\n".join(os.listdir(abs_path))
        
        with open(abs_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        start, end = (view_range if view_range else [1, len(lines)])
        if end == -1: end = len(lines)
        
        output = [f"{i}: {lines[i-1].rstrip()}" for i in range(start, min(end + 1, len(lines) + 1))]
        return "\n".join(output)

    def create(self, path: str, file_text: str) -> str:
        abs_path = self._validate_path(path)
        if os.path.exists(abs_path):
            return "Error: File already exists."
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(file_text)
        return f"Successfully created {path}"

# 3. Tool Schema for Gemini
TOOLS = [
    {
        "name": "text_editor",
        "description": "A tool to view, create, or edit local files.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "enum": ["view", "create"]},
                "path": {"type": "string", "description": "Path to the file"},
                "file_text": {"type": "string", "description": "Content for create command"},
                "view_range": {"type": "array", "items": {"type": "integer"}, "description": "[start_line, end_line]"}
            },
            "required": ["command", "path"]
        }
    }
]

# 4. Orchestration Functions
editor = TextEditorTool()

def run_tool_logic(name, args):
    if name == "text_editor":
        cmd = args["command"]
        if cmd == "view":
            return editor.view(args["path"], args.get("view_range"))
        elif cmd == "create":
            return editor.create(args["path"], args.get("file_text", ""))
    return f"Error: Unknown tool {name}"

def chat_with_gemini(user_prompt):
    messages = [{"role": "user", "content": user_prompt}]
    
    while True:
        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=1024,
            messages=messages,
            tools=TOOLS
        )
        
        # Add assistant response to history
        messages.append({"role": "assistant", "content": response.content})
        
        if response.stop_reason != "tool_use":
            # Return the final text content
            return "".join([b.text for b in response.content if b.type == "text"])

        # Handle Tool Calls
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"--- Running Tool: {block.name} ({block.input['command']}) ---")
                result = run_tool_logic(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result)
                })
        
        messages.append({"role": "user", "content": tool_results})

# 5. Execution
if __name__ == "__main__":
    prompt = "open file calculator_using_gemini.py and write an python code for a simple calculator"
    final_answer = chat_with_gemini(prompt)
    print(f"\nGemini's Response:\n{final_answer}")