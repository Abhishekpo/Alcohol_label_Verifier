from app.services.validation_service import (
    extract_alcohol_percentage,
    validate_net_contents,
    validate_text_field,
    validate_government_warning,
)

def test_extracts_alcohol_percentage_with_slash():
    extracted_text = "40% ALC./VOL. (80 PROOF)"

    result = extract_alcohol_percentage(extracted_text)

    assert result == 40.0


def test_handles_ocr_separator_error():
    extracted_text = "40% ALC.IVOL. (80 PROOF)"

    result = extract_alcohol_percentage(extracted_text)

    assert result == 40.0


def test_returns_none_when_alcohol_percentage_is_missing():
    extracted_text = "Premium triple-distilled vodka"

    result = extract_alcohol_percentage(extracted_text)

    assert result is None

def test_matches_ml_when_fl_oz_appears_first():
    extracted_text = "12 FL. OZ. (355 mL)"

    result = validate_net_contents(
        expected_text="355 ml",
        extracted_text=extracted_text
    )

    assert result["status"] == "PASS"


def test_matches_equivalent_fl_oz_and_ml():
    result = validate_net_contents(
        expected_text="12 fl oz",
        extracted_text="355 mL"
    )

    assert result["status"] == "PASS"


def test_matches_liters_and_milliliters():
    result = validate_net_contents(
        expected_text="1 l",
        extracted_text="1000 mL"
    )

    assert result["status"] == "PASS"


def test_fails_for_different_net_contents():
    result = validate_net_contents(
        expected_text="500 ml",
        extracted_text="355 mL"
    )

    assert result["status"] == "FAIL"


def test_needs_review_when_net_contents_are_missing():
    result = validate_net_contents(
        expected_text="750 ml",
        extracted_text="Premium bourbon whiskey"
    )

    assert result["status"] == "NEEDS_REVIEW"

def test_brand_name_passes_despite_case_difference():
    result = validate_text_field(
        field_name="brand_name",
        expected_text="Stone's Throw",
        extracted_text="STONE'S THROW"
    )

    assert result["status"] == "PASS"


def test_brand_name_fails_for_different_text():
    result = validate_text_field(
        field_name="brand_name",
        expected_text="OLD TOM DISTILLERY",
        extracted_text="SILVER FOX VODKA"
    )

    assert result["status"] == "FAIL"

def test_warning_passes_with_extra_sulfites_statement():
    extracted_text = """
    GOVERNMENT WARNING: (1) ACCORDING TO
    THE SURGEON GENERAL, WOMEN SHOULD NOT
    DRINK ALCOHOLIC BEVERAGES DURING
    PREGNANCY BECAUSE OF THE RISK OF BIRTH
    DEFECTS. (2) CONSUMPTION OF ALCOHOLIC
    BEVERAGES IMPAIRS YOUR ABILITY TO DRIVE A
    CAR OR OPERATE MACHINERY, AND MAY CAUSE
    HEALTH PROBLEMS. CONTAINS SULFITES
    """

    result = validate_government_warning(extracted_text)

    assert result["status"] == "PASS"
    assert result["similarity_score"] == 100.0

def test_class_type_split_across_lines_passes():
    extracted_text = """
    ABC WINERY
    AMERICAN
    MERLOT
    ALC. 15.5% BY VOL.
    """

    result = validate_text_field(
        field_name="class_type",
        expected_text="American Merlot",
        extracted_text=extracted_text
    )

    assert result["status"] == "PASS"
    assert result["detected"] == "AMERICAN MERLOT"
    assert result["similarity_score"] == 100.0

def test_brand_name_split_across_lines_passes():
    extracted_text = """
    ABC WINERY

    AMERICAN
    MERLOT
    """

    result = validate_text_field(
        field_name="brand_name",
        expected_text="ABC Winery",
        extracted_text=extracted_text
    )

    assert result["status"] == "PASS"
    assert result["detected"] == "ABC WINERY"
    assert result["similarity_score"] == 100.0