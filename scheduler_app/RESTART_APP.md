# How to Restart the Flask App to Enable Barcodes

## The Issue
The barcode libraries are installed, but the Flask app needs to be restarted to:
1. Load the updated code with barcode support
2. Import the barcode libraries

## Quick Fix

### Option 1: Using the start script (Recommended)
```bash
# Stop the current app (if running)
# Then restart:
./start.sh    # On Linux/Mac
start.bat     # On Windows
```

### Option 2: Manual restart
If you're running the app manually:
1. **Stop the Flask app** (Ctrl+C in the terminal where it's running)
2. **Start it again**:
   ```bash
   python app.py
   # or
   flask run
   ```

### Option 3: If running as a service
If the app is running as a Windows service or systemd service:
```bash
# Windows Service
net stop flask-scheduler
net start flask-scheduler

# Linux systemd
sudo systemctl restart flask-scheduler
```

## Verify It's Working

After restarting, check the application logs. You should see:
```
✓ Barcode libraries loaded successfully
```

If you see this warning instead:
```
⚠ Barcode libraries not available: No module named 'barcode'
```

Then the Flask app is using a different Python environment. You'll need to install the libraries in that environment:

```bash
# Find which Python the Flask app is using
which python     # Linux/Mac
where python     # Windows

# Install in that environment
pip install python-barcode Pillow
```

## Check Installation

Run this diagnostic script to verify:
```bash
cd scheduler_app
python check_barcode_support.py
```

You should see all "[OK]" messages.

## After Restart

1. Go to the Printing section
2. Generate a Daily Items List
3. Barcodes should now appear instead of "N/A"

## Troubleshooting

### Still seeing N/A after restart?

Check the Flask application logs for error messages. The new code will show:
- "✓ Barcode libraries loaded successfully" - Good!
- "⚠ Barcode libraries not available" - Libraries not found in Flask's Python environment
- "Failed to generate barcode for XXXXX" - Specific barcode generation errors

### If you're using a virtual environment:

Make sure you activate it first:
```bash
# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate

# Then install
pip install python-barcode Pillow

# Then restart the app
python app.py
```
