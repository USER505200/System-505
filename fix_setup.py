import os
import re

def fix_setup(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Find the class name
    class_match = re.search(r'class (\w+)\(commands\.Cog\):', content)
    if not class_match:
        return
    class_name = class_match.group(1)
    
    # Replace the setup
    old_setup = r'async def setup\(bot\):\s*bot\.add_cog\(' + re.escape(class_name) + r'\(bot\)\)'
    new_setup = f'def setup(bot):\n    cog = {class_name}(bot)\n    bot.add_cog(cog)\n    return cog'
    
    if re.search(old_setup, content):
        new_content = re.sub(old_setup, new_setup, content)
        with open(file_path, 'w') as f:
            f.write(new_content)
        print(f"Fixed {file_path}")

for root, dirs, files in os.walk('cogs'):
    for file in files:
        if file.endswith('.py'):
            fix_setup(os.path.join(root, file))