import re
from rapidfuzz import fuzz
import math

REQUIRED_GOVERNMENT_WARNING = (
    "GOVERNMENT WARNING: (1) According to the Surgeon General, women "
    "should not drink alcoholic beverages during pregnancy because of the "
    "risk of birth defects. (2) Consumption of alcoholic beverages impairs "
    "your ability to drive a car or operate machinery, and may cause health "
    "problems."
)


# this function normalizes the text by converting it to lowercase, removing apostrophes, and 
# replacing non-alphanumeric characters with spaces. It also collapses multiple spaces into a single 
# space and trims leading/trailing whitespace.
def normalize_text(text: str) -> str:
    normalized = text.casefold()
    normalized = normalized.replace("'", "").replace("’", "")
    normalized = re.sub(r"[^a-z0-9\s]", " ", normalized) # replace non-alphanumeric characters with space
    normalized = re.sub(r"\s+", " ", normalized) # collapse multiple spaces into one

    return normalized.strip()

# This function finds the best matching line from the extracted text for a given expected text.
def find_best_line_match(
    expected_text: str,
    extracted_text: str
) -> tuple[str | None, float]:

    lines = [
        line.strip()
        for line in extracted_text.splitlines()
        if line.strip()
    ]

    expected_normalized = normalize_text(expected_text)

    best_detected_text = None
    best_score = 0.0

    for index, line in enumerate(lines):
        candidates = [line]

        # Combine two neighboring OCR lines
        if index + 1 < len(lines):
            candidates.append(
                f"{line} {lines[index + 1]}"
            )

        # Combine three neighboring OCR lines
        if index + 2 < len(lines):
            candidates.append(
                f"{line} {lines[index + 1]} "
                f"{lines[index + 2]}"
            )

        for candidate in candidates:
            score = fuzz.ratio(
                expected_normalized,
                normalize_text(candidate)
            )

            if score > best_score:
                best_score = score
                best_detected_text = candidate

    return best_detected_text, round(best_score, 2)

# This function determines the match status based on the similarity score.
def get_match_status(score: float) -> str:
    if score >= 90:
        return "PASS"

    if score >= 75:
        return "NEEDS_REVIEW"

    return "FAIL"

# This function validates a text field by comparing the expected text with the extracted text and returns a 
# dictionary containing the validation results.
def validate_text_field(
    field_name: str,
    expected_text: str,
    extracted_text: str
) -> dict:

    detected_text, score = find_best_line_match(
        expected_text,
        extracted_text
    )

    status = get_match_status(score)

    return {
        "field": field_name,
        "expected": expected_text,
        "detected": detected_text,
        "similarity_score": score,
        "status": status
    }

# This function extracts the alcohol percentage from the extracted text using a regular expression pattern.
def extract_alcohol_percentage(extracted_text: str) -> float | None:
    strict_pattern = (
        r"(\d+(?:\.\d+)?)\s*%"
        r"\s*alc(?:ohol)?\.?"
        r"\s*(?:by\s*|[/|iIlL]\s*)?"
        r"vol(?:ume)?\.?"
    )

    strict_match = re.search(
        strict_pattern,
        extracted_text,
        re.IGNORECASE
    )

    if strict_match is not None:
        return float(strict_match.group(1))

    # Safe fallback: accept a percentage only when exactly one exists.
    percentage_pattern = r"(\d+(?:\.\d+)?)\s*%"
    percentage_matches = re.findall(
        percentage_pattern,
        extracted_text
    )

    if len(percentage_matches) == 1:
        return float(percentage_matches[0])

    return None

"""
if Tesseract does not detect a percentage, we don’t know whether:

The label is missing it.
The text is too small.
The image is unclear.
OCR failed.

Therefore, a human should review it.
"""

def validate_alcohol_percentage(
    expected_percentage: float,
    extracted_text: str
) -> dict:

    detected_percentage = extract_alcohol_percentage(
        extracted_text
    )

    if detected_percentage is None:
        return {
            "field": "alcohol_percentage",
            "expected": expected_percentage,
            "detected": None,
            "status": "NEEDS_REVIEW",
            "reason": "Alcohol percentage could not be detected."
        }

    values_match = math.isclose(
        expected_percentage,
        detected_percentage,
        abs_tol=0.01
    )

    return {
        "field": "alcohol_percentage",
        "expected": expected_percentage,
        "detected": detected_percentage,
        "status": "PASS" if values_match else "FAIL",
        "reason": (
            "Alcohol percentages match."
            if values_match
            else (
                "Label alcohol percentage does not "
                "match the application."
            )
        )
    }

# This function normalizes the volume by converting liters to milliliters if necessary.
def normalize_volume(
    amount: float,
    unit: str
) -> float:

    normalized_unit = re.sub(r"[\s.]+", "", unit.lower())

    if normalized_unit == "l":
        return amount * 1000

    if normalized_unit == "floz":
        return amount * 29.5735

    return amount  

# This function extracts the net contents (volume) from the extracted text using a regular expression pattern.
def extract_all_net_contents(
    text: str
) -> list[tuple[float, str]]:

    pattern = r"\b(\d+(?:\.\d+)?)\s*(mL|L|fl\.?\s*oz\.?)\b"

    matches = re.finditer(
        pattern,
        text,
        re.IGNORECASE
    )

    results = []

    for match in matches:
        amount = float(match.group(1))
        unit = match.group(2).lower()
        unit = re.sub(r"[\s.]+", "", unit)

        results.append((amount, unit))

    return results

def validate_net_contents(
    expected_text: str,
    extracted_text: str
) -> dict:

    expected_values = extract_all_net_contents(expected_text)
    detected_values = extract_all_net_contents(extracted_text)

    if not expected_values:
        return {
            "field": "net_contents",
            "expected": expected_text,
            "detected": None,
            "status": "NEEDS_REVIEW",
            "reason": "Application net contents could not be understood."
        }

    if not detected_values:
        return {
            "field": "net_contents",
            "expected": expected_text,
            "detected": None,
            "status": "NEEDS_REVIEW",
            "reason": "Net contents could not be detected on the label."
        }

    expected_amount, expected_unit = expected_values[0]
    expected_ml = normalize_volume(
        expected_amount,
        expected_unit
    )

    matching_value = None

    for detected_amount, detected_unit in detected_values:
        detected_ml = normalize_volume(
            detected_amount,
            detected_unit
        )

        if math.isclose(
            expected_ml,
            detected_ml,
            abs_tol=1.0
        ):
            matching_value = (
                detected_amount,
                detected_unit
            )
            break

    values_match = matching_value is not None

    if matching_value:
        displayed_value = (
            f"{matching_value[0]:g} {matching_value[1]}"
        )
    else:
        displayed_value = ", ".join(
            f"{amount:g} {unit}"
            for amount, unit in detected_values
        )

    return {
        "field": "net_contents",
        "expected": expected_text,
        "detected": displayed_value,
        "status": "PASS" if values_match else "FAIL",
        "reason": (
            "Net contents match."
            if values_match
            else "Label net contents do not match the application."
        )
    }

# This function validates the government warning by checking if the required warning text is present in the extracted text 
# and returns a dictionary containing the validation results.
def validate_government_warning(extracted_text: str) -> dict:
    collapsed_text = " ".join(extracted_text.split())

    normalized_expected = normalize_text(
        REQUIRED_GOVERNMENT_WARNING
    )
    normalized_extracted = normalize_text(
        collapsed_text
    )

    # Required warning exists, even if capitalization,
    # punctuation, line breaks, or extra text differ.
    if normalized_expected in normalized_extracted:
        return {
            "field": "government_warning",
            "expected": REQUIRED_GOVERNMENT_WARNING,
            "detected": REQUIRED_GOVERNMENT_WARNING,
            "similarity_score": 100.0,
            "status": "PASS",
            "reason": "The required warning text was detected."
        }

    warning_marker = normalize_text("GOVERNMENT WARNING")
    warning_start = normalized_extracted.find(warning_marker)

    if warning_start == -1:
        return {
            "field": "government_warning",
            "expected": REQUIRED_GOVERNMENT_WARNING,
            "detected": None,
            "similarity_score": 0.0,
            "status": "NEEDS_REVIEW",
            "reason": "The government warning could not be detected."
        }

    normalized_detected_warning = normalized_extracted[
        warning_start:
    ]

    score = fuzz.partial_ratio(
        normalized_expected,
        normalized_detected_warning
    )

    status = "NEEDS_REVIEW" if score >= 85 else "FAIL"

    return {
        "field": "government_warning",
        "expected": REQUIRED_GOVERNMENT_WARNING,
        "detected": collapsed_text,
        "similarity_score": round(score, 2),
        "status": status,
        "reason": (
            "The warning was detected but contains possible OCR differences."
            if status == "NEEDS_REVIEW"
            else "The detected warning differs significantly from the required text."
        )
    }
    
def calculate_overall_status(
    validation_results: list[dict]
) -> str:

    statuses = {
        result["status"]
        for result in validation_results
    }

    if "FAIL" in statuses:
        return "FAIL"

    if "NEEDS_REVIEW" in statuses:
        return "NEEDS_REVIEW"

    return "PASS"