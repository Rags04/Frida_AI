"""
Helper script to load Frida scripts from the external Frida-Mobile-Scripts-master folder
and generate Python dictionary entries
"""
import os
import re
from pathlib import Path

# Path to external scripts
EXTERNAL_SCRIPTS_PATH = r"c:\Users\LENOVO\Downloads\Frida-Mobile-Scripts-master\Frida-Mobile-Scripts-master\Android"

def extract_description(script_content):
    """Extract description from script header comment"""
    lines = script_content.split('\n')
    description = "No description available"
    
    for line in lines[:20]:  # Check first 20 lines for description
        if 'Name:' in line:
            description = line.split('Name:')[1].strip().rstrip('*/').strip()
            break
        elif 'Description:' in line:
            description = line.split('Description:')[1].strip().rstrip('*/').strip()
            break
    
    return description

def format_script_for_python(content):
    """Format script content for Python string literal"""
    # Escape backslashes and quotes
    formatted = content.replace('\\', '\\\\').replace('"""', r'\"\"\"')
    return formatted

def load_external_scripts():
    """Load all scripts from external folder"""
    scripts = {}
    
    if not os.path.exists(EXTERNAL_SCRIPTS_PATH):
        print(f"External scripts path not found: {EXTERNAL_SCRIPTS_PATH}")
        return scripts
    
    # Get all .js files
    js_files = sorted([f for f in os.listdir(EXTERNAL_SCRIPTS_PATH) if f.endswith('.js')])
    
    print(f"Found {len(js_files)} JavaScript files in {EXTERNAL_SCRIPTS_PATH}")
    print("-" * 80)
    
    for filename in js_files:
        filepath = os.path.join(EXTERNAL_SCRIPTS_PATH, filename)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract description from header
            description = extract_description(content)
            
            # Create script name from filename
            script_name = filename.replace('_', ' ').replace('.js', '').title()
            
            scripts[script_name] = {
                "description": description,
                "content": content,
                "filename": filename
            }
            
            print(f"✓ {script_name}")
            print(f"  File: {filename}")
            print(f"  Desc: {description[:70]}...")
            print()
        
        except Exception as e:
            print(f"✗ Error loading {filename}: {str(e)}")
            print()
    
    return scripts

def generate_python_code(scripts):
    """Generate Python dictionary code for all scripts"""
    code_lines = []
    
    for script_name, info in scripts.items():
        # Create safe Python identifier
        safe_name = repr(script_name)
        description = info['description'][:100]  # Limit description length
        
        # Use raw string for script content
        script_content = info['content']
        
        code_lines.append(f'    {safe_name}: {{')
        code_lines.append(f'        "description": {repr(description)},')
        code_lines.append(f'        "script": r"""')
        code_lines.append(script_content)
        code_lines.append(f'""",')
        code_lines.append(f'    }},')
        code_lines.append('')
    
    return '\n'.join(code_lines)

if __name__ == "__main__":
    scripts = load_external_scripts()
    print("\n" + "=" * 80)
    print(f"Total scripts loaded: {len(scripts)}")
    print("=" * 80)
    
    # Generate and save code
    if scripts:
        print("\nGenerating Python code...")
        python_code = generate_python_code(scripts)
        
        # Save to a temp file
        output_file = "external_scripts_generated.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# GENERATED EXTERNAL SCRIPTS - Copy this into BYPASS_SCRIPTS dictionary\n\n")
            f.write(python_code)
        
        print(f"✓ Generated code saved to: {output_file}")
