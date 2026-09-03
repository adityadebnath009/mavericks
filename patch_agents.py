import os

files = [
    "backend/tests/test_marine_agent.py",
    "backend/tests/test_planner_agent.py",
    "backend/tests/test_weather_agent.py"
]

for file_path in files:
    with open(file_path, "r") as f:
        content = f.read()
    
    if "import pytest" not in content:
        content = "import pytest\n" + content
        
    content = content.replace("async def test_", "@pytest.mark.asyncio\nasync def test_")
    
    with open(file_path, "w") as f:
        f.write(content)
