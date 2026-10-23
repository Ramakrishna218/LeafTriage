import streamlit as st
from PIL import Image
from predict import load_model_and_labels, predict_image

st.set_page_config(page_title="LeafTriage", page_icon="🌿", layout="wide")

st.title("🌿 LeafTriage")
st.subheader("Trust-first tomato leaf disease triage")

st.info(
    "AI predictions are preliminary and are not confirmed diagnoses."
)

@st.cache_resource
def get_model():
    return load_model_and_labels()

try:
    model, labels = get_model()
except Exception as exc:
    st.error(f"Unable to load the model: {exc}")
    st.stop()

language = st.selectbox("Guidance language / வழிகாட்டும் மொழி",
                        ["English", "தமிழ்"])

uploaded = st.file_uploader(
    "Upload a tomato leaf photo",
    type=["jpg", "jpeg", "png"]
)

if uploaded:
    try:
        image = Image.open(uploaded).convert("RGB")
        st.image(image, caption="Selected leaf", use_container_width=True)

        if st.button("Analyze leaf", type="primary"):
            with st.spinner("Analyzing image locally..."):
                predictions = predict_image(image, model, labels)

            top = predictions[0]
            st.subheader("AI prediction")
            st.write(top["class"].replace("Tomato___", "").replace("_", " "))
            st.metric("Model score", f"{top['score'] * 100:.2f}%")

            st.subheader("Ranked predictions")
            for item in predictions:
                st.write(
                    f"{item['class'].replace('Tomato___', '').replace('_', ' ')}"
                    f" — {item['score'] * 100:.2f}%"
                )

            st.warning(
                "A model score is not a verified probability. "
                "Confirm uncertain or concerning symptoms with an agricultural expert."
            )

    except Exception as exc:
        st.error(f"Could not process this image: {exc}")

st.divider()
st.caption(
    "LeafTriage currently supports only three tomato leaf classes."
)
