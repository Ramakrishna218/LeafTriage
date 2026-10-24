
import streamlit as st
from PIL import Image
from supabase import create_client, Client
from predict import load_model_and_labels, predict_image
import socket
from urllib.parse import urlparse
import requests
import numpy as np
from tensorflow import keras
import json
from pathlib import Path


st.set_page_config(
    page_title="LeafTriage",
    page_icon="🌿",
    layout="wide"
)


@st.cache_resource
def get_model():
    return load_model_and_labels()

BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"

@st.cache_resource
def load_crop_model(crop_name):
    model_files = {
        "Tomato": ("tomato_model_clean.keras", "class_names.json"),
        "Grape": ("grape_model.keras", "grape_class_names.json"),
        "Paddy": ("paddy_model.keras", "paddy_class_names.json"),
    }

    model_file, labels_file = model_files[crop_name]
    model_path = MODELS_DIR / model_file
    labels_path = MODELS_DIR / labels_file

    if not model_path.is_file():
        raise FileNotFoundError(f"Model file not found: {model_path}")

    if not labels_path.is_file():
        raise FileNotFoundError(f"Label file not found: {labels_path}")

    model = keras.models.load_model(model_path)

    with open(labels_path, "r", encoding="utf-8") as f:
        labels = json.load(f)

    return model, labels

@st.cache_resource
def load_crop_model(crop_name):
    model_files = {
        "Tomato": ("models/tomato_model_clean.keras", "models/class_names.json"),
        "Grape": ("models/grape_model.keras", "models/grape_class_names.json"),
        "Paddy": ("models/paddy_model.keras", "models/paddy_class_names.json"),
    }

    model_path, labels_path = model_files[crop_name]

    model = keras.models.load_model(model_path)

    with open(labels_path, "r") as f:
        labels = json.load(f)

    return model, labels


def fetch_rows(table, params=None):
    base_url = st.secrets["SUPABASE_URL"].strip().rstrip("/")
    api_key = st.secrets["SUPABASE_KEY"]

    response = requests.get(
        f"{base_url}/rest/v1/{table}",
        headers={
            "apikey": api_key,
            "Authorization": f"Bearer {api_key}",
        },
        params=params or {"select": "*"},
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


def show_value(title, value):
    if value:
        st.markdown(f"### {title}")
        st.write(value)

st.title("🌿 LeafTriage")
st.write("Crop growing guidance and AI-assisted tomato leaf triage.")


# Connect to Supabase

url = st.secrets["SUPABASE_URL"]
host = urlparse(url).hostname

try:
    result = socket.getaddrinfo(host, 443)
   
except socket.gaierror as exc:
    st.error(f"DNS lookup failed for {host}: {exc}")

url = st.secrets["SUPABASE_URL"].strip().rstrip("/")
host = urlparse(url).hostname


try:
    response = requests.get(
        f"{url}/rest/v1/crops?select=id&limit=1",
        headers={
            "apikey": st.secrets["SUPABASE_KEY"],
            "Authorization": f"Bearer {st.secrets['SUPABASE_KEY']}",
        },
        timeout=15,
    )
   
except Exception as exc:
    st.error(f"Direct API test failed: {type(exc).__name__}: {exc}")


try:
    crops = fetch_rows("crops", {"select": "*", "order": "id"})
except Exception as exc:
    st.error(f"Could not load crops: {exc}")
    st.stop()

if not crops:
    st.warning("No crops found in the database.")
    st.stop()

# Crop navigation
st.subheader("🌱 Explore crops")

columns = st.columns(3)

for index, crop in enumerate(crops):
    with columns[index % 3]:
        if st.button(
            crop["display_name"],
            key=f"crop_{crop['id']}",
            use_container_width=True
        ):
            st.session_state.selected_crop = crop["id"]

selected_id = st.session_state.get("selected_crop")

if selected_id:
    selected = next(
        (crop for crop in crops if crop["id"] == selected_id),
        None
    )

    if selected:
        st.divider()
        st.header(f"🌱 {selected['display_name']} Growing Guide")

        if selected.get("local_name"):
            st.caption(selected["local_name"])

        show_value("About this crop", selected.get("description"))

        guides = fetch_rows(
    "planting_guides",
    {"select": "*", "crop_id": f"eq.{selected_id}"}
)

        if guides:
            guide = guides[0]

            sections = [
                ("Soil requirements", "soil_requirements"),
                ("Climate requirements", "climate_requirements"),
                ("Land preparation", "land_preparation"),
                ("Seed selection", "seed_selection"),
                ("Nursery preparation", "nursery_preparation"),
                ("Sowing or transplanting", "sowing_or_transplanting"),
                ("Planting method", "planting_method"),
                ("Spacing", "spacing"),
                ("Irrigation", "irrigation"),
                ("Crop care", "crop_care"),
                ("Weed management", "weed_management"),
                ("Harvesting", "harvest_guidance"),
                ("Growing duration", "growing_duration"),
            ]

            for title, field in sections:
                show_value(title, guide.get(field))

            if guide.get("source_name"):
                st.caption(f"Source: {guide['source_name']}")

            if guide.get("source_url"):
                st.markdown(
                    f"[Read the agricultural source]({guide['source_url']})"
                )
        else:
            st.info(
                "The detailed growing guide for this crop "
                "has not been added yet."
            )

        fertilizer_rows = fetch_rows(
    "fertilizer_guides",
    {"select": "*", "crop_id": f"eq.{selected_id}"}
)

        st.subheader("🧪 Fertilizer guidance")

        if fertilizer_rows:
            for item in fertilizer_rows:
                st.markdown(f"#### {item['fertilizer_name']}")
                show_value("Nutrients", item.get("nutrient_details"))
                show_value("Application stage", item.get("application_stage"))
                show_value("Application method", item.get("application_method"))
                show_value("Recommended dose", item.get("recommended_dose"))
                show_value("Precautions", item.get("precautions"))
                if item.get("source_url"):
                    st.markdown(f"[Source]({item['source_url']})")
        else:
            st.info(
                "Verified fertilizer recommendations are not available "
                "for this crop yet. Check local soil-test results and "
                "agricultural department recommendations."
            )

        disease_rows = fetch_rows(
    "disease_guides",
    {"select": "*", "crop_id": f"eq.{selected_id}"}
)

        st.subheader("🍃 Disease information")

        if disease_rows:
            for item in disease_rows:
                st.markdown(f"#### {item['disease_name']}")
                show_value("Symptoms", item.get("symptoms"))
                show_value(
                    "Management guidance",
                    item.get("management_guidance")
                )
                if item.get("source_url"):
                    st.markdown(f"[Source]({item['source_url']})")
        else:
            st.info("Disease guides have not been added yet.")

        if st.button("← Back to crop selection"):
            del st.session_state.selected_crop
            st.rerun()

# Existing tomato leaf prediction
st.divider()

st.divider()
st.header("🔬 AI Leaf Disease Diagnosis")

selected_crop = st.selectbox(
    "Select crop",
    ["Tomato", "Grape", "Paddy"]
)

uploaded = st.file_uploader(
    f"Upload a {selected_crop.lower()} leaf photo",
    type=["jpg", "jpeg", "png"],
    key=f"leaf_upload_{selected_crop}"
)

if uploaded:
    image = Image.open(uploaded).convert("RGB")
    st.image(image, caption="Uploaded leaf", use_container_width=True)

    if st.button("Analyze leaf", type="primary"):
        try:
            model, labels = load_crop_model(selected_crop)

            if selected_crop == "Tomato":
                predictions = predict_image(image, model, labels)
                predicted_class = str(predictions[0]["class"])
            else:
                # Grape and Paddy models were trained at 224 x 224
                resized = image.resize((224, 224))
                image_array = np.asarray(resized, dtype=np.float32)
                image_array = np.expand_dims(image_array, axis=0)

                scores = model.predict(image_array, verbose=0)[0]
                predicted_class = str(labels[int(np.argmax(scores))])

            normalized = (
                predicted_class.lower()
                .replace("tomato___", "")
                .replace("grape___", "")
                .replace("paddy___", "")
                .replace("_", " ")
                .replace("(", "")
                .replace(")", "")
                .strip()
            )

            guidance = DISEASE_GUIDANCE[selected_crop.lower()]

            matched_key = next(
                (
                    key for key in guidance
                    if key in normalized or normalized in key
                ),
                None
            )

            if matched_key is None:
                st.subheader("Disease identification uncertain")
                st.write(
                    "No matching remedy is configured for this model label. "
                    "Please consult an agricultural expert."
                )
            else:
                if matched_key == "healthy":
                    st.subheader(f"Healthy {selected_crop} Leaf")
                else:
                    st.subheader(
                        f"{matched_key.title()} — {selected_crop}"
                    )

                st.markdown("### Recommended Remedy")
                st.write(guidance[matched_key])

            st.warning(
                "AI results may be incorrect. Confirm uncertain or severe "
                "cases with a local agricultural expert."
            )
        except Exception as exc:
            st.error(f"Could not analyze the image: {exc}")




