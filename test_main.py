import os
import pytest
import hashlib
from PIL import Image
from main import (
    compute_image_hash,
    extract_metadata,
    compare_metadata,
    perform_pixel_comparison
)

# Set up test paths
TEST_IMAGES_DIR = os.path.join(os.path.dirname(__file__), 'test_images')
ORIGINAL_IMAGE = os.path.join(TEST_IMAGES_DIR, 'original.jpg')
TAMPERED_IMAGE = os.path.join(TEST_IMAGES_DIR, 'tampered.jpg')
DIFFERENT_IMAGE = os.path.join(TEST_IMAGES_DIR, 'different.jpg')
NON_EXISTENT_IMAGE = os.path.join(TEST_IMAGES_DIR, 'ghost.jpg')

@pytest.fixture(scope="module")
def setup_test_images():
    """Create test images if they don't exist"""
    os.makedirs(TEST_IMAGES_DIR, exist_ok=True)
    
    # Create original test image
    if not os.path.exists(ORIGINAL_IMAGE):
        img = Image.new('RGB', (100, 100), color='red')
        img.save(ORIGINAL_IMAGE)
    
    # Create tampered version (single pixel changed)
    if not os.path.exists(TAMPERED_IMAGE):
        img = Image.open(ORIGINAL_IMAGE)
        pixels = img.load()
        pixels[47, 48] = (0, 255, 0)  # Change one pixel to green
        img.save(TAMPERED_IMAGE)
    
    # Create completely different image
    if not os.path.exists(DIFFERENT_IMAGE):
        img = Image.new('RGB', (100, 100), color='blue')
        img.save(DIFFERENT_IMAGE)

def test_compute_image_hash(setup_test_images):
    """Test SHA-256 hash computation for images"""
    # Hash should be consistent for same image
    hash1 = compute_image_hash(ORIGINAL_IMAGE)
    hash2 = compute_image_hash(ORIGINAL_IMAGE)
    assert hash1 == hash2
    
    # Hash should be different for different images
    hash_original = compute_image_hash(ORIGINAL_IMAGE)
    hash_tampered = compute_image_hash(TAMPERED_IMAGE)
    hash_different = compute_image_hash(DIFFERENT_IMAGE)
    assert hash_original != hash_tampered
    assert hash_original != hash_different
    assert hash_tampered != hash_different

def test_extract_metadata(setup_test_images):
    """Test metadata extraction from images"""
    # Test basic metadata extraction
    meta = extract_metadata(ORIGINAL_IMAGE)
    assert 'Format' in meta
    assert 'Dimensions' in meta
    assert 'File Size' in meta
    
    # Verify dimensions are correct
    assert meta['Dimensions'] == (100, 100)
    
    # Test with non-existent image (should raise SystemExit)
    with pytest.raises(SystemExit):
        extract_metadata(NON_EXISTENT_IMAGE)

def test_compare_metadata():
    """Test metadata comparison between images"""
    meta1 = extract_metadata(ORIGINAL_IMAGE)
    
    assert compare_metadata(meta1, meta1) is True

def test_perform_pixel_comparison(capsys):
    """Test pixel-level comparison between images"""
    # Test with identical images
    perform_pixel_comparison(ORIGINAL_IMAGE, ORIGINAL_IMAGE)
    captured = capsys.readouterr()
    assert "No visual differences detected" in captured.out
    
    # Test with tampered image (single pixel changed)
    perform_pixel_comparison(ORIGINAL_IMAGE, TAMPERED_IMAGE)
    captured = capsys.readouterr()
    assert "Modified Pixels" in captured.out
    assert "(47, 48)" in captured.out  # Should find our changed pixel
    
    # Test with different sized images
    small_img = os.path.join(TEST_IMAGES_DIR, 'small.jpg')
    Image.new('RGB', (50, 50), color='red').save(small_img)
    perform_pixel_comparison(ORIGINAL_IMAGE, small_img)
    captured = capsys.readouterr()
    assert "different dimensions" in captured.out
    os.remove(small_img)

def test_hash_algorithm_consistency():
    """Verify the hash algorithm produces expected results"""
    test_file = os.path.join(TEST_IMAGES_DIR, 'hash_test.txt')
    with open(test_file, 'w') as f:
        f.write("PixelGuard test string")
    
    # Manually compute expected hash
    hasher = hashlib.sha256()
    with open(test_file, 'rb') as f:
        while chunk := f.read(4096):
            hasher.update(chunk)
    expected_hash = hasher.hexdigest()
    
    # Compare with function output
    assert compute_image_hash(test_file) == expected_hash
    os.remove(test_file)

def test_metadata_fields_completeness(setup_test_images):
    """Verify all expected metadata fields are present"""
    meta = extract_metadata(ORIGINAL_IMAGE)
    required_fields = ['Format', 'Dimensions', 'File Size']
    for field in required_fields:
        assert field in meta
    assert isinstance(meta['Dimensions'], tuple)
    assert isinstance(meta['File Size'], int)

def test_pixel_comparison_limits(setup_test_images, capsys):
    """Test the max_pixels and display_limit parameters"""
    # Should only check up to max_pixels (default 100)
    perform_pixel_comparison(ORIGINAL_IMAGE, DIFFERENT_IMAGE, max_pixels=5)
    captured = capsys.readouterr()
    assert "checked up to 5" in captured.out
    
    # Should only display up to display_limit (default 20)
    perform_pixel_comparison(ORIGINAL_IMAGE, DIFFERENT_IMAGE, display_limit=3)
    captured = capsys.readouterr()
    assert "Sample modified pixels" in captured.out
    assert "..." in captured.out  # Indicates truncation