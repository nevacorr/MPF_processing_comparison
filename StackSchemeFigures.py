from PIL import Image
import os

image_path = "/Users/nevao/Documents/MPF_Project/files_for_making_figures/workflow figures"
scale = 0.90

# Crop approximately one inch from each side of image 1.
fallback_dpi = 300
side_crop_inches = 1.0

# Shift the right column left by this many pixels.
# Increase this value to bring the images even closer together.
column_overlap = 200

img1 = Image.open(os.path.join(image_path, "Parcellation Scheme.png"))
img2 = Image.open(os.path.join(image_path, "Mean MPF scheme.png"))
img3 = Image.open(os.path.join(image_path, "Volumes Scheme.png"))

# Convert one inch to pixels using image 1's horizontal DPI.
dpi_x = img1.info.get("dpi", (fallback_dpi, fallback_dpi))[0]
side_crop_pixels = round(side_crop_inches * dpi_x)
side_crop_pixels = min(side_crop_pixels, (img1.width - 1) // 2)

img1 = img1.crop(
    (side_crop_pixels, 0, img1.width - side_crop_pixels, img1.height)
)


def shrink_on_same_canvas(img, horizontal_alignment="center"):
    """Shrink content to 90% while retaining the image's canvas size."""
    img = img.convert("RGBA")
    resized = img.resize(
        (round(img.width * scale), round(img.height * scale)),
        Image.Resampling.LANCZOS,
    )

    canvas = Image.new("RGBA", img.size, "white")

    if horizontal_alignment == "right":
        x = canvas.width - resized.width
    else:
        x = (canvas.width - resized.width) // 2

    y = (canvas.height - resized.height) // 2
    canvas.alpha_composite(resized, (x, y))
    return canvas.convert("RGB")


# Symmetrically crop images 2 and 3 to the same width.
right_width = min(img2.width, img3.width)
right_images = []

for img in (img2, img3):
    excess_width = img.width - right_width
    left = excess_width // 2
    cropped = img.crop((left, 0, left + right_width, img.height))
    right_images.append(shrink_on_same_canvas(cropped))

# Right-align image 1's scaled content within its column.
img1 = shrink_on_same_canvas(img1, horizontal_alignment="right")
img2, img3 = right_images

right_column_height = img2.height + img3.height

# Move the right column left so the two groups sit closer together.
column_overlap = max(0, min(column_overlap, img1.width - 1))
right_x = img1.width - column_overlap

final_width = right_x + right_width
final_height = max(img1.height, right_column_height)
final = Image.new("RGB", (final_width, final_height), "white")

# Vertically center image 1 in the left column.
img1_y = (final_height - img1.height) // 2
final.paste(img1, (0, img1_y))

# Vertically center the stacked pair in the right column.
right_y = (final_height - right_column_height) // 2
final.paste(img2, (right_x, right_y))
final.paste(img3, (right_x, right_y + img2.height))

output_path = os.path.join(image_path, "combined.png")
# final.save(output_path)
final.show()

print(f"Cropped {side_crop_pixels} pixels from each side of image 1.")
print(f"Shifted the right column left by {column_overlap} pixels.")
print(f"Saved combined image to: {output_path}")
