
from PIL import Image, ImageDraw, ImageFont
import os

image_path = "/Users/nevao/Documents/MPF_Project/files_for_making_figures/workflow figures"
scale = 0.90

# Crop approximately one inch from each side of image 1.
fallback_dpi = 300
side_crop_inches = 1.0

# Shift the right column left by this many pixels.
column_overlap = 80

# Border and label settings.
box_color = "black"
box_width = 4
label_font_size = 84
label_padding = 12
label_background_padding = 5

# Independently adjust each box using pixel values in this order:
# (left, top, right, bottom)
# Positive values move an edge inward and make the box smaller.
# Negative values move an edge outward and make the box larger.
# For example, top=-80 and bottom=-80 make the box 160 pixels taller.
panel_box_insets = {
    "A": (70, -80, 90, -106),
    "B": (20, 77, 40, 70),
    "C": (20, -50, 40, 50),
}

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


def load_bold_font(size):
    """Load a commonly available bold font, with a Pillow fallback."""
    font_paths = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "DejaVuSans-Bold.ttf",
    ]

    for font_path in font_paths:
        try:
            return ImageFont.truetype(font_path, size)
        except OSError:
            continue

    return ImageFont.load_default()


def adjust_box(box, adjustments):
    """Adjust box edges inward with positive values or outward with negatives."""
    left, top, right, bottom = box
    adjust_left, adjust_top, adjust_right, adjust_bottom = adjustments

    adjusted = (
        left + adjust_left,
        top + adjust_top,
        right - adjust_right,
        bottom - adjust_bottom,
    )

    if adjusted[0] >= adjusted[2] or adjusted[1] >= adjusted[3]:
        raise ValueError(
            f"Box adjustments {adjustments} are too large for panel box {box}."
        )

    return adjusted


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
img2_y = right_y
img3_y = right_y + img2.height
final.paste(img2, (right_x, img2_y))
final.paste(img3, (right_x, img3_y))

# Original panel bounds before applying each panel's custom adjustments.
base_panel_boxes = {
    "A": (0, img1_y, img1.width - 1, img1_y + img1.height - 1),
    "B": (right_x, img2_y, right_x + img2.width - 1, img2_y + img2.height - 1),
    "C": (right_x, img3_y, right_x + img3.width - 1, img3_y + img3.height - 1),
}

# Draw independently sized boxes and their panel letters.
draw = ImageDraw.Draw(final)
font = load_bold_font(label_font_size)

for label in "ABC":
    left, top, right, bottom = adjust_box(
        base_panel_boxes[label], panel_box_insets[label]
    )

    # Keep expanded boxes within the final image canvas.
    left = max(0, left)
    top = max(0, top)
    right = min(final.width - 1, right)
    bottom = min(final.height - 1, bottom)

    stroke_inset = box_width // 2
    draw.rectangle(
        (
            left + stroke_inset,
            top + stroke_inset,
            right - stroke_inset,
            bottom - stroke_inset,
        ),
        outline=box_color,
        width=box_width,
    )

    label_x = left + box_width + label_padding + 10
    label_y = top + box_width + label_padding
    text_box = draw.textbbox((label_x, label_y), label, font=font)
    background_box = (
        text_box[0] - label_background_padding,
        text_box[1] - label_background_padding,
        text_box[2] + label_background_padding,
        text_box[3] + label_background_padding,
    )
    draw.rectangle(background_box, fill="white")
    draw.text((label_x, label_y), label, fill="black", font=font)

output_path = os.path.join(image_path, "WorkflowSchemeFigure.png")
final.save(output_path)
final.show()

# print(f"Cropped {side_crop_pixels} pixels from each side of image 1.")
# print(f"Shifted the right column left by {column_overlap} pixels.")
# print("Added independently adjustable boxes and labels A, B, and C.")
# print(f"Saved combined image to: {output_path}")