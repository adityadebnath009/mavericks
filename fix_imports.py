import os
import glob
test_files = glob.glob("backend/tests/**/*.py", recursive=True)
for file_path in test_files:
    with open(file_path, 'r') as f:
        content = f.read()
    if "VesselProfile(" in content and "import VesselProfile" not in content:
        # replace the OrcaBsiEngine import to include VesselProfile
        content = content.replace("import OrcaBsiEngine", "import OrcaBsiEngine, VesselProfile")
        # or just add it at the top if it wasn't added
        if "import OrcaBsiEngine, VesselProfile" not in content:
             content = "from app.api.services.orca_bsi_engine import VesselProfile\n" + content
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"Fixed {file_path}")
