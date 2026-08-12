from PIL import Image, ImageOps 

def preprocess_image(image: Image.Image) -> Image.Image:
    image = ImageOps.exif_transpose(image)  # Some phone images store their orientation as metadata instead 
                                            #of physically rotating the pixels. This applies that orientation correctly.
    image = image.convert("L")              # Convert to grayscale
    image = ImageOps.autocontrast(image)    # Apply autocontrast to enhance the image contrast

    return image
