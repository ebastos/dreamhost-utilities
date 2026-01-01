from main import main
import io
import sys
import subprocess

def test_main_smoke():
    # Capture stdout
    captured_output = io.StringIO()
    sys.stdout = captured_output
    try:
        main()
    finally:
        sys.stdout = sys.__stdout__
    
    assert "Hello from dreamhost-utilities!" in captured_output.getvalue()

def test_main_script_execution():
    # Test that the script runs correctly as a subprocess
    result = subprocess.run([sys.executable, "main.py"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "Hello from dreamhost-utilities!" in result.stdout

