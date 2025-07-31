#!/usr/bin/env python3
"""
Comprehensive test to understand the three-frame logic in AutoDocTemplate
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

def test_original_frame_logic():
    """Test the original frame creation logic to understand the three-frame behavior"""
    print("=" * 70)
    print("Testing Original Frame Logic in AutoDocTemplate")
    print("=" * 70)
    
    try:
        import autobasedoc.autorpt as ar
        
        # Test 1: Single column (frameCount = 0)
        print("\n1. Testing Single Column (frameCount = 0)")
        print("-" * 50)
        
        doc_single = ar.AutoDocTemplate(
            "test_single.pdf",
            onFirstPage=(ar.drawFirstPortrait, 0),
            onLaterPages=(ar.drawLaterPortrait, 0),
            debug=True
        )
        
        template = doc_single.getTemplate(temp_id="FirstPortrait")
        if template:
            print(f"Template ID: {template.id}")
            print(f"Number of frames: {len(template.frames)}")
            for i, frame in enumerate(template.frames):
                print(f"  Frame {i}: {frame.id}")
                print(f"    Position: x1={frame._x1}, y1={frame._y1}")
                print(f"    Size: width={frame._width}, height={frame._height}")
        
        # Test 2: Two columns (frameCount = 2)
        print("\n2. Testing Two Columns (frameCount = 2)")
        print("-" * 50)
        
        doc_multi = ar.AutoDocTemplate(
            "test_multi.pdf",
            onFirstPage=(ar.drawFirstLandscape, 2),
            onLaterPages=(ar.drawLaterLandscape, 2),
            debug=True
        )
        
        template = doc_multi.getTemplate(temp_id="FirstLandscape")
        if template:
            print(f"Template ID: {template.id}")
            print(f"Number of frames: {len(template.frames)}")
            for i, frame in enumerate(template.frames):
                print(f"  Frame {i}: {frame.id}")
                print(f"    Position: x1={frame._x1}, y1={frame._y1}")
                print(f"    Size: width={frame._width}, height={frame._height}")
                print(f"    Padding: left={frame._leftPadding}, bottom={frame._bottomPadding}")
        
        # Test 3: Three columns (frameCount = 3)
        print("\n3. Testing Three Columns (frameCount = 3)")
        print("-" * 50)
        
        doc_three = ar.AutoDocTemplate(
            "test_three.pdf",
            onFirstPage=(ar.drawFirstLandscape, 3),
            onLaterPages=(ar.drawLaterLandscape, 3),
            debug=True
        )
        
        template = doc_three.getTemplate(temp_id="FirstLandscape")
        if template:
            print(f"Template ID: {template.id}")
            print(f"Number of frames: {len(template.frames)}")
            for i, frame in enumerate(template.frames):
                print(f"  Frame {i}: {frame.id}")
                print(f"    Position: x1={frame._x1}, y1={frame._y1}")
                print(f"    Size: width={frame._width}, height={frame._height}")
        
        # Test 4: Test getFrame method behavior
        print("\n4. Testing getFrame Method Behavior")
        print("-" * 50)
        
        # Test with template name
        try:
            frame, pagesize = doc_multi.getFrame("FirstLandscape")
            print(f"getFrame('FirstLandscape') returned: {frame.id}")
            print(f"Page size: {pagesize}")
        except Exception as e:
            print(f"getFrame error: {e}")
        
        # Test with orientation
        try:
            frame, pagesize = doc_multi.getFrame(orientation="Landscape0")
            print(f"getFrame(orientation='Landscape0') returned: {frame.id}")
        except Exception as e:
            print(f"getFrame orientation error: {e}")
            
        # Test with full template id
        try:
            frame, pagesize = doc_multi.getFrame("FirstLandscape", orientation="FirstLandscape")
            print(f"getFrame with full template id returned: {frame.id}")
        except Exception as e:
            print(f"getFrame full template id error: {e}")
        
        return True
        
    except Exception as e:
        print(f"Error in frame logic test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_frame_usage_patterns():
    """Test how frames are actually used in document creation"""
    print("\n\n5. Testing Frame Usage Patterns")
    print("-" * 50)
    
    try:
        import autobasedoc.autorpt as ar
        from autobasedoc.styles import Styles
        from reportlab.platypus import Paragraph
        
        # Create a document with multiple frames
        doc = ar.AutoDocTemplate(
            "test_usage.pdf",
            onFirstPage=(ar.drawFirstLandscape, 2),
            onLaterPages=(ar.drawLaterLandscape, 2),
        )
        
        styles = Styles()
        content = []
        
        # Add some content
        content.append(Paragraph("Test Title", styles.title))
        content.append(Paragraph("This is test content " * 50, styles.normal))
        
        # Try to build the document
        doc.build(content)
        print("✓ Document built successfully with multi-column layout")
        
        # Check if PDF was created
        if os.path.exists("test_usage.pdf"):
            file_size = os.path.getsize("test_usage.pdf")
            print(f"✓ PDF created: test_usage.pdf ({file_size} bytes)")
        
        return True
        
    except Exception as e:
        print(f"✗ Error in usage test: {e}")
        import traceback
        traceback.print_exc()
        return False

def analyze_frame_purpose():
    """Analyze the purpose of the additional frame"""
    print("\n\n6. Analyzing Frame Purpose")
    print("-" * 50)
    
    try:
        import autobasedoc.autorpt as ar
        
        # Create test document
        doc = ar.AutoDocTemplate(
            "test_analyze.pdf",
            onFirstPage=(ar.drawFirstLandscape, 2),
            debug=True
        )
        
        template = doc.getTemplate(temp_id="FirstLandscape")
        if template and len(template.frames) > 2:
            print("Frame analysis:")
            for i, frame in enumerate(template.frames):
                print(f"Frame {i} ({frame.id}):")
                print(f"  - Position: ({frame._x1}, {frame._y1})")
                print(f"  - Size: {frame._width} x {frame._height}")
                print(f"  - Covers full page: {frame._x1 == 0 and frame._y1 == 0}")
                print(f"  - Full page size: {frame._width == template.pagesize[0] and frame._height == template.pagesize[1]}")
                
                # Check if this frame overlaps with column frames
                if i > 0:  # Skip first frame
                    first_frame = template.frames[0]
                    overlaps = (frame._x1 < first_frame._x1 + first_frame._width and 
                               frame._x1 + frame._width > first_frame._x1)
                    print(f"  - Overlaps with column frames: {overlaps}")
                print()
        
        return True
        
    except Exception as e:
        print(f"Error in analysis: {e}")
        return False

def main():
    """Run all tests"""
    print("AutoBaseDoc Frame Logic Analysis")
    print("Testing original unchanged version")
    
    tests = [
        test_original_frame_logic,
        test_frame_usage_patterns,
        analyze_frame_purpose,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"Test failed: {e}")
            results.append(False)
    
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests passed: {sum(results)}/{len(results)}")
    
    if all(results):
        print("✓ All tests completed successfully")
        print("\nConclusions:")
        print("- The three-frame structure appears to be intentional")
        print("- Need to understand the purpose of the additional full-page frame")
    else:
        print("✗ Some tests failed")
    
    # Clean up test files
    for filename in ["test_single.pdf", "test_multi.pdf", "test_three.pdf", "test_usage.pdf", "test_analyze.pdf"]:
        if os.path.exists(filename):
            try:
                os.remove(filename)
                print(f"Cleaned up {filename}")
            except:
                pass

if __name__ == "__main__":
    main()
