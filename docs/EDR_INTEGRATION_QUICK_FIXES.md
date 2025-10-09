# EDR Integration - Final Touches

## ✅ Completed Files

1. **scheduler_app/services/edr_service.py** - ✅ Complete
2. **scheduler_app/utils/event_helpers.py** - ✅ Complete
3. **tests/test_pdf_generator.py** - ✅ Complete
4. **tests/test_edr_service.py** - ✅ Complete
5. **docs/architecture/edr-integration-architecture.md** - ✅ Complete

## 🔧 Minor Fixes Needed

### 1. PDF Generator (`edr_downloader/pdf_generator.py`)

**Line 188** - Add one line to make "Locked" value BOLD:

```python
# Current (line 187-190):
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, 1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),

# Should be (add line after 188):
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, 1), 'Helvetica'),
                ('FONTNAME', (3, 1), (3, 1), 'Helvetica-Bold'),  # Bold for Locked value
                ('FONTSIZE', (0, 0), (-1, -1), 10),
```

**Optional - Lines 37, 260** - Change "Place" to "Staple":
- Line 37: Change `text="Place Price Signs Here"` to `text="Staple Price Signs Here"`
- Line 260: Change comment from "Place" to "Staple"

## 📝 Next Steps

1. Update `scheduler_app/routes/printing.py` - Add 3 new EDR endpoints
2. Verify `scheduler_app/templates/printing.html` - Frontend code
3. Test the integration

## Manual Fix Command

If you want to manually add the bold line:

```bash
# Open the file
nano edr_downloader/pdf_generator.py

# Navigate to line 188 and add after it:
                ('FONTNAME', (3, 1), (3, 1), 'Helvetica-Bold'),  # Bold for Locked value
```

Or use this sed command:

```bash
sed -i "188a\\                ('FONTNAME', (3, 1), (3, 1), 'Helvetica-Bold'),  # Bold for Locked value" edr_downloader/pdf_generator.py
```
