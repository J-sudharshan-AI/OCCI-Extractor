import streamlit as st
import re
from paddleocr import PaddleOCR
import pandas as pd
import numpy as np
import cv2

# -----------------------------
# INIT OCR (load once)
# -----------------------------
@st.cache_resource
def load_ocr():
    return PaddleOCR(use_angle_cls=True, lang='en')

ocr = load_ocr()


# -----------------------------
# CLEAN + EXTRACT LOGIC
# -----------------------------
def is_valid_value(text):
    if len(text) <= 2:
        return False
    if re.fullmatch(r"[A-Za-z]", text):
        return False
    return True


def find_next_valid(lines, i):
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

        if "CR" in line and "No" in line:
            val = find_next_valid(lines, i)
            nums = re.findall(r"\d+", val)
            if nums:
                data["CR_No"] = nums[0]

        elif "Registered" in line and "grade" in line:
            data["Grade"] = find_next_valid(lines, i)

        elif "OCCI" in line:
            val = find_next_valid(lines, i)
            nums = re.findall(r"\d+", val)
            if nums:
                data["OCCI_No"] = nums[0]

        elif "issue" in line.lower():
            val = find_next_valid(lines, i)
            match = re.findall(r"\d{2}/\d{2}/\d{4}", val)
            if match:
                data["Issue_Date"] = match[0]

        elif "expiry" in line.lower():
            val = find_next_valid(lines, i)
            match = re.findall(r"\d{2}/\d{2}/\d{4}", val)
            if match:
                data["Expiry_Date"] = match[0]

        elif "Head Office" in line:
            data["Head_Office"] = find_next_valid(lines, i)

    return data


# -----------------------------
# STREAMLIT UI
# -----------------------------
st.title("📄 OCCI Certificate Extractor")

uploaded_file = st.file_uploader("Upload Certificate Image", type=["png", "jpg", "jpeg"])

if uploaded_file:

    # Convert to OpenCV format
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    image = cv2.imdecode(file_bytes, 1)

    st.image(image, caption="Uploaded Image", use_container_width=True)

    with st.spinner("Processing..."):

        result = ocr.ocr(image)

        lines = []
        for line in result[0]:
            text = line[1][0]
            text = re.sub(r"[^\x00-\x7F]+", " ", text).strip()
            if text:
                lines.append(text)

        fields = extract_occi(lines)

    st.success("Extraction Complete ✅")

    st.subheader("📊 Extracted Data")

    # 🔥 Convert dictionary → clean table format
    df_display = pd.DataFrame(list(fields.items()), columns=["Field", "Value"])

    # Optional: beautify field names
    df_display["Field"] = df_display["Field"].replace({
        "CR_No": "CR No",
        "OCCI_No": "OCCI No",
        "Issue_Date": "Issue Date",
        "Expiry_Date": "Expiry Date",
        "Head_Office": "Head Office"
    })

    # Display as grid
    st.dataframe(df_display, use_container_width=True)

    # -----------------------------
    # Download CSV (original format)
    # -----------------------------
    df_download = pd.DataFrame([fields])

    csv = df_download.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="⬇ Download CSV",
        data=csv,
        file_name="occi_result.csv",
        mime="text/csv"
    )