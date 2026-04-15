import re
from paddleocr import PaddleOCR

# -----------------------------
# INIT OCR
# -----------------------------
ocr = PaddleOCR(use_angle_cls=True, lang='en')

image_path = r"F:\OCCI\input\img.png"


# -----------------------------
# STEP 1: OCR → TEXT LINES
# -----------------------------
result = ocr.ocr(image_path)

lines = []

for line in result[0]:
    text = line[1][0]

    # remove Arabic / noise
    text = re.sub(r"[^\x00-\x7F]+", " ", text).strip()

    if text:
        lines.append(text)


print("\n--- OCR LINES ---")
for l in lines:
    print(l)


# -----------------------------
# STEP 2: OCCI FIELD EXTRACTION
# -----------------------------

import re

def is_valid_value(text):
    """Reject garbage OCR lines"""
    if len(text) <= 2:
        return False
    if re.fullmatch(r"[A-Za-z]", text):
        return False
    return True


def find_next_valid(lines, i):
    """Look ahead for valid value"""
    for j in range(i+1, min(i+4, len(lines))):
        if is_valid_value(lines[j]):
            return lines[j]
    return ""


def extract_occi(lines):
    data = {
        "CR_No": "",
        "Grade": "",
        "OCCI_No": "",
        "Issue_Date": "",
        "Expiry_Date": "",
        "Head_Office": ""
    }

    for i, line in enumerate(lines):

        # CR No
        if "CR" in line and "No" in line:
            val = find_next_valid(lines, i)
            nums = re.findall(r"\d+", val)
            if nums:
                data["CR_No"] = nums[0]

        # Grade
        elif "Registered" in line and "grade" in line:
            val = find_next_valid(lines, i)
            data["Grade"] = val

        # OCCI No
        elif "OCCI" in line:
            val = find_next_valid(lines, i)
            nums = re.findall(r"\d+", val)
            if nums:
                data["OCCI_No"] = nums[0]

        # Issue Date
        elif "issue" in line.lower():
            val = find_next_valid(lines, i)
            match = re.findall(r"\d{2}/\d{2}/\d{4}", val)
            if match:
                data["Issue_Date"] = match[0]

        # Expiry Date
        elif "expiry" in line.lower():
            val = find_next_valid(lines, i)
            match = re.findall(r"\d{2}/\d{2}/\d{4}", val)
            if match:
                data["Expiry_Date"] = match[0]

        # Head Office
        elif "Head Office" in line:
            val = find_next_valid(lines, i)
            data["Head_Office"] = val

    return data


# -----------------------------
# STEP 3: RUN EXTRACTION
# -----------------------------
fields = extract_occi(lines)

print("\n--- FINAL OUTPUT ---")
print(fields)