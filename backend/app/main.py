from app.services.ocr_service import extract_text
from fastapi import FastAPI, HTTPException, Form
from fastapi import UploadFile, File
from time import perf_counter
from fastapi.middleware.cors import CORSMiddleware
import csv
from io import StringIO
from typing import List
import os
from app.services.validation_service import (validate_text_field,
                                             validate_alcohol_percentage,
                                             validate_net_contents,
                                             validate_government_warning,
                                             calculate_overall_status,
                                             )


app = FastAPI()

frontend_url = os.getenv(
    "FRONTEND_URL",
    "http://localhost:5173"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        frontend_url
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# only these image types are allowed for upload
ALLOWED_IMAGE_TYPES = {
    "image/png",
    "image/jpeg",
    "image/webp"
}
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB


@app.get("/health")
def health_check():
    return {"status": "healthy",
            "ocr_engine": "tesseract"
        }


def process_label(
    image_bytes: bytes,
    filename: str,
    content_type: str,
    brand_name: str,
    class_type: str,
    alcohol_percentage: float,
    net_contents: str
) -> dict:

    start_time = perf_counter()

    extracted_text = extract_text(image_bytes)

    brand_result = validate_text_field(
        field_name="brand_name",
        expected_text=brand_name,
        extracted_text=extracted_text
    )

    class_result = validate_text_field(
        field_name="class_type",
        expected_text=class_type,
        extracted_text=extracted_text
    )

    alcohol_result = validate_alcohol_percentage(
        expected_percentage=alcohol_percentage,
        extracted_text=extracted_text
    )

    net_contents_result = validate_net_contents(
        expected_text=net_contents,
        extracted_text=extracted_text
    )

    warning_result = validate_government_warning(
        extracted_text=extracted_text
    )

    validation_results = [
        brand_result,
        class_result,
        alcohol_result,
        net_contents_result,
        warning_result
    ]

    overall_status = calculate_overall_status(
        validation_results
    )

    processing_time_ms = round(
        (perf_counter() - start_time) * 1000,
        2
    )

    return {
        "filename": filename,
        "content_type": content_type,
        "size_bytes": len(image_bytes),
        "extracted_text": extracted_text,
        "application_data": {
            "brand_name": brand_name,
            "class_type": class_type,
            "alcohol_percentage": alcohol_percentage,
            "net_contents": net_contents
        },
        "validation_results": validation_results,
        "overall_status": overall_status,
        "processing_time_ms": processing_time_ms
    }


@app.post("/verify")
async def verify_label(image: UploadFile = File(...),
                       brand_name: str = Form(...),
                       class_type: str = Form(...),
                       alcohol_percentage: float = Form(..., ge=0, le=100),
                       net_contents: str = Form(...)):
    start_time = perf_counter()
    if image.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=415,
            detail="Only PNG, JPEG, and WebP images are supported."
        )

    # Read the image bytes to ensure it's not empty
    image_bytes = await image.read(MAX_IMAGE_SIZE + 1)
    if len(image_bytes) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="The image must be 10 MB or smaller."
        )
    if not image_bytes:
        raise HTTPException(
            status_code=400,
            detail="The uploaded image is empty."
        )

    return process_label(
        image_bytes=image_bytes,
        filename=image.filename or "unknown",
        content_type=image.content_type or "unknown",
        brand_name=brand_name,
        class_type=class_type,
        alcohol_percentage=alcohol_percentage,
        net_contents=net_contents
    )


@app.post("/verify-batch")
async def verify_batch(
    images: List[UploadFile] = File(...),
    csv_file: UploadFile = File(...)
):
    if not csv_file.filename or not csv_file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=415,
            detail="The application-data file must be a CSV file."
        )

    csv_bytes = await csv_file.read()

    if not csv_bytes:
        raise HTTPException(
            status_code=400,
            detail="The uploaded CSV file is empty."
        )

    try:
        csv_text = csv_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="The CSV file must use UTF-8 encoding."
        )

    reader = csv.DictReader(StringIO(csv_text))

    required_columns = {
        "filename",
        "brand_name",
        "class_type",
        "alcohol_percentage",
        "net_contents"
    }

    if reader.fieldnames is None:
        raise HTTPException(
            status_code=400,
            detail="The CSV file does not contain a header row."
        )

    missing_columns = required_columns - set(reader.fieldnames)

    if missing_columns:
        raise HTTPException(
            status_code=400,
            detail=(
                "CSV is missing required columns: "
                + ", ".join(sorted(missing_columns))
            )
        )

    rows = list(reader)

    if not rows:
        raise HTTPException(
            status_code=400,
            detail="The CSV file does not contain any application records."
        )

    image_map = {
        image.filename: image
        for image in images
        if image.filename
    }

    

    batch_results = []
    
    batch_errors = []

    for row in rows:
        filename = row.get("filename", "").strip()

        if filename not in image_map:
            batch_errors.append({
                "filename": filename or "Unknown",
                "error": "No matching uploaded image was found."
            })
            continue

    
   
        image = image_map[filename]
        

        try:
            alcohol_percentage = float(
                row["alcohol_percentage"].strip()
            )
        except (TypeError, ValueError):
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid alcohol percentage for {filename}: "
                    f"{row['alcohol_percentage']}"
                )
            )

        if not 0 <= alcohol_percentage <= 100:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Alcohol percentage for {filename} "
                    "must be between 0 and 100."
                )
            )

        if image.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=415,
                detail=f"{filename} is not a supported image type."
            )

        image_bytes = await image.read(MAX_IMAGE_SIZE + 1)

        if len(image_bytes) > MAX_IMAGE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"{filename} must be 10 MB or smaller."
            )

        if not image_bytes:
            raise HTTPException(
                status_code=400,
                detail=f"{filename} is empty."
            )

        result = process_label(
            image_bytes=image_bytes,
            filename=filename,
            content_type=image.content_type or "unknown",
            brand_name=row["brand_name"].strip(),
            class_type=row["class_type"].strip(),
            alcohol_percentage=alcohol_percentage,
            net_contents=row["net_contents"].strip()
        )

        batch_results.append(result)

    status_counts = {
        "PASS": 0,
        "FAIL": 0,
        "NEEDS_REVIEW": 0
    }

    for result in batch_results:
      status = result["overall_status"]
      status_counts[status] += 1

    return {
        "total_records": len(rows),
        "processed": len(batch_results),
        "error_count": len(batch_errors),
        "status_counts": status_counts,
        "errors": batch_errors,
        "results": batch_results
        }
