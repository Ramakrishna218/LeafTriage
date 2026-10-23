
import streamlit as st
from PIL import Image
from supabase import create_client, Client
from predict import load_model_and_labels, predict_image
import socket
from urllib.parse import urlparse
import requests


st.set_page_config(
    page_title="LeafTriage",
    page_icon="🌿",
    layout="wide"
)


@st.cache_resource
def get_model():
    return load_model_and_labels()

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
st.info(
    "AI predictions are preliminary. They are not confirmed diagnoses."
)

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
st.header("🔬 Tomato Leaf Disease Triage")

try:
    model, labels = get_model()

    uploaded = st.file_uploader(
        "Upload a tomato leaf photo",
        type=["jpg", "jpeg", "png"]
    )

    if uploaded:
        image = Image.open(uploaded).convert("RGB")
        st.image(image, caption="Selected leaf", use_container_width=True)

        DISEASE_NAMES = {
    "early blight": "Early Blight of Tomato (Alternaria solani)",
    "late blight": "Late Blight of Tomato (Phytophthora infestans)",
    "healthy": "Healthy Tomato Leaf"
}

       if st.button("Analyze leaf", type="primary"):
    predictions = predict_image(image, model, labels)

    if predictions:
        predicted_class = (
            predictions[0]["class"]
            .replace("Tomato___", "")
            .replace("_", " ")
            .strip()
            .lower()
        )

        DISEASE_NAMES = {
            "early blight": "Early Blight of Tomato (Alternaria solani)",
            "late blight": "Late Blight of Tomato (Phytophthora infestans)",
            "healthy": "Healthy Tomato Leaf"
        }

        REMEDIES = {
            "early blight": (
                "Remove severely affected leaves, avoid wetting foliage "
                "during irrigation, and improve airflow around plants. "
                "Consult a local agricultural expert if the disease spreads."
            ),
            "late blight": (
                "Remove severely infected plant material safely, avoid "
                "prolonged leaf wetness, and promptly consult an agricultural "
                "expert about suitable locally approved treatments."
            ),
            "healthy": (
                "No disease was identified by the model. Continue monitoring "
                "the plant and maintain good crop hygiene."
            )
        }

        st.subheader(DISEASE_NAMES.get(
            predicted_class, "Disease identification uncertain"
        ))

        st.markdown("### Recommended Remedy")
        st.write(REMEDIES.get(
            predicted_class,
            "No verified remedy is available for this prediction. "
            "Please consult an agricultural expert."
        ))

        st.warning(
            "This is an AI-assisted prediction, not a confirmed diagnosis."
        )

    else:
        st.warning("No prediction returned. Please try another leaf photo.")

except Exception as exc:
    st.error(f"Could not load the prediction model: {exc}")


