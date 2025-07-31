#!/usr/bin/env python3
"""
Test script to verify all fixes and check for errors in autobasedoc
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

def test_imports():
    """Test all imports work correctly"""
    print("Testing imports...")
    import autobasedoc.autorpt as ar
    import autobasedoc.autoplot as ap
    import autobasedoc.styles as styles
    import autobasedoc.pageinfo as pageinfo
    import autobasedoc.fonts as fonts
    import autobasedoc.styledtable as styledtable
    import autobasedoc.tableofcontents as toc
    print("✓ All imports successful")
    assert ar is not None
    assert ap is not None
    assert styles is not None

def test_basic_functionality():
    """Test basic functionality"""
    print("Testing basic functionality...")
    import autobasedoc.autorpt as ar
    
    # Test AutoDocTemplate creation
    doc = ar.AutoDocTemplate(
        "test_output.pdf",
        onFirstPage=(ar.drawFirstPortrait, 0),
        onLaterPages=(ar.drawLaterPortrait, 0),
        title="Test Document",
        author="Test Author",
        producer="AutoBaseDoc Test"
    )
    print("✓ AutoDocTemplate created successfully")
    assert doc is not None
    assert doc.title == "Test Document"
    
    # Test Bookmark creation
    bookmark = ar.Bookmark("Test Section", level=1)
    print(f"✓ Bookmark created: {bookmark.title}, key: {bookmark.key}")
    assert bookmark.title == "Test Section"
    assert bookmark.level == 1
    assert bookmark.key is not None
    
    # Test Table of Contents
    toc = ar.doTableOfContents()
    print("✓ Table of contents created successfully")
    assert toc is not None
    
    # Test styles
    from autobasedoc.styles import Styles
    styles = Styles()
    print("✓ Styles loaded successfully")
    assert styles is not None

def test_frame_logic():
    """Test the frame logic"""
    print("Testing frame logic...")
    import autobasedoc.autorpt as ar
    
    # Test multi-column template creation
    doc = ar.AutoDocTemplate(
        "test_multicolumn.pdf",
        onFirstPage=(ar.drawFirstLandscape, 2),  # 2 columns
        onLaterPages=(ar.drawLaterLandscape, 2),
    )
    
    # Get a template to test frame logic
    template = doc.getTemplate(temp_id="FirstLandscape")
    assert template is not None, "Template not found"
    print(f"✓ Template found: {template.id}")
    print(f"✓ Number of frames: {len(template.frames)}")
    assert len(template.frames) == 3, f"Expected 3 frames, got {len(template.frames)}"
    
    # Test getFrame method
    frame, pagesize = doc.getFrame("FirstLandscape")
    print(f"✓ Frame retrieved: {frame.id}, pagesize: {pagesize}")
    assert frame is not None
    assert pagesize is not None

# Clean up test files after all tests
def teardown_module():
    """Clean up test files after all tests"""
    import os
    for filename in ["test_output.pdf", "test_multicolumn.pdf"]:
        if os.path.exists(filename):
            try:
                os.remove(filename)
                print(f"Cleaned up {filename}")
            except:
                pass
