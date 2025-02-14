import os
import hashlib
from PIL import Image, ImageChops
from PIL.ExifTags import TAGS

def get_image_path(prompt):
    """Prompt user for an image filename and return the full path."""
    filename = input(prompt)
    path = f"./images/{filename}"

    if not os.path.exists(path):
        print("❌ Error: File does not exist. Please check the filename.")
        exit(1)
    
    return path

def compute_image_hash(image_path):
    """Generate SHA-256 hash of an image."""
    hasher = hashlib.sha256()
    with open(image_path, "rb") as img_file:
        while chunk := img_file.read(4096):
            hasher.update(chunk)
    return hasher.hexdigest()

def generate_hash_for_original():
    """Option 1: Generate and print the hash of an original image."""
    original_path = get_image_path("Enter the original image filename (with extension): ")
    image_hash = compute_image_hash(original_path)
    
    print("\n🔹 SHA-256 Hash of Original Image:")
    print(image_hash)
    print("\n💾 Store this hash securely for future verification.")

def compare_with_stored_hash():
    """Option 2: Compare a suspect image's hash with a stored original hash."""
    suspect_path = get_image_path("Enter the suspect image filename (with extension): ")
    stored_hash = input("Enter the previously stored hash of the original image: ")

    suspect_hash = compute_image_hash(suspect_path)

    print("\n🔍 SHA-256 Hash Comparison:")
    print(f"Stored Original Hash: {stored_hash}")
    print(f"Suspect Image Hash:   {suspect_hash}")

    if suspect_hash == stored_hash:
        print("\n✅ No tampering detected. The suspect image matches the original.")
    else:
        print("\n⚠️  Tampering detected! The suspect image does NOT match the original.")

def extract_metadata(image_path):
    """Extract key metadata fields (Format, Dimensions, File Size)."""
    try:
        with Image.open(image_path) as img:
            metadata = {
                "Format": img.format,
                "Dimensions": img.size,  # (width, height)
                "File Size": os.path.getsize(image_path)  # in bytes
            }
            
            # Extract EXIF metadata if available
            exif_data = img._getexif()
            if exif_data:
                for tag, value in exif_data.items():
                    tag_name = TAGS.get(tag, tag)
                    metadata[tag_name] = value
        
        return metadata

    except Exception as e:
        print(f"⚠️  Error reading metadata: {e}")
        exit(1)

def compare_metadata(meta1, meta2):
    """Compare key metadata fields. Return True if they match, False otherwise."""
    keys_to_compare = ["Format", "Dimensions", "File Size"]
    
    differences = {key: (meta1[key], meta2[key]) for key in keys_to_compare if meta1[key] != meta2[key]}

    if differences:
        print("\n⚠️  Metadata Mismatch! Possible tampering detected.\n")
        for key, (original_val, suspect_val) in differences.items():
            print(f"{key}: Original = {original_val}, Suspect = {suspect_val}")
        return False  # Metadata mismatch

    print("\n✅ Metadata matches. Proceeding to hash comparison...")
    return True  # Metadata matches

def compare_images():
    """Option 3: Compare two images (original vs suspect)."""
    original_path = get_image_path("Enter the original image filename (with extension): ")
    suspect_path = get_image_path("Enter the suspect image filename (with extension): ")

    original_metadata = extract_metadata(original_path)
    suspect_metadata = extract_metadata(suspect_path)

    # Step 1: Compare Metadata
    if compare_metadata(original_metadata, suspect_metadata):
        # Step 2: Compare Hashes (only if metadata matches)
        original_hash = compute_image_hash(original_path)
        suspect_hash = compute_image_hash(suspect_path)

        print("\n🔍 SHA-256 Hash Comparison:")
        print(f"Original: {original_hash}")
        print(f"Suspect:  {suspect_hash}")

        if original_hash == suspect_hash:
            print("\n✅ No tampering detected. The images are identical.")
        else:
            print("\n⚠️  Tampering detected! The images have been modified.")
            perform_pixel_comparison(original_path, suspect_path)

def perform_pixel_comparison(original_path, suspect_path, max_pixels=100, display_limit=20):
    """Perform pixel-level comparison to detect modified pixels."""
    try:
        with Image.open(original_path) as img1, Image.open(suspect_path) as img2:
            img1 = img1.convert("RGB")
            img2 = img2.convert("RGB")

            if img1.size != img2.size:
                print("\n❌ Images have different dimensions. Skipping pixel comparison.")
                return

            diff = ImageChops.difference(img1, img2)
            diff_pixels = diff.getbbox()  # Get bounding box of changed region

            if not diff_pixels:
                print("\n⚠️  No visual differences detected, but hash mismatched (possible metadata-only change).")
                return

            # Finding exact modified pixel locations (limited scan)
            modified_pixels = []
            count = 0
            for x in range(img1.width):
                for y in range(img1.height):
                    if img1.getpixel((x, y)) != img2.getpixel((x, y)):
                        modified_pixels.append((x, y))
                        count += 1
                        if count >= max_pixels:
                            break
                if count >= max_pixels:
                    break

            # Generate report
            print(f"\n🔍 Pixel-Level Analysis Report:")
            print(f"Total Modified Pixels (checked up to {max_pixels}): {len(modified_pixels)}")

            # Show sample modified pixels (limiting display)
            if len(modified_pixels) > display_limit:
                print(f"Sample modified pixels: {modified_pixels[:display_limit]} ...")
            else:
                print(f"Modified pixels: {modified_pixels}")

    except Exception as e:
        print(f"⚠️ Error in pixel comparison: {e}")

# Main Menu
def main():
    while True:
        print("\n📌 Select an option:")
        print("1️⃣  Generate a hash for an original image")
        print("2️⃣  Compare a suspect image with a stored hash")
        print("3️⃣  Compare two images (original and suspect)")
        print("0️⃣  Exit")
        
        choice = input("\nEnter your choice (0-3): ").strip()

        if choice == "1":
            generate_hash_for_original()
        elif choice == "2":
            compare_with_stored_hash()
        elif choice == "3":
            compare_images()
        elif choice == "0":
            print("\n👋 Exiting. Have a great day!")
            break
        else:
            print("\n❌ Invalid choice. Please enter a number between 0 and 3.")

# Run the script
if __name__ == "__main__":
    main()
