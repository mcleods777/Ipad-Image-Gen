import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import base64
import os

# Set page config
st.set_page_config(page_title="Gemini Image Creator", layout="wide")

# Initialize the Gemini client
def initialize_client():
    api_key = st.secrets.get("GOOGLE_API_KEY", os.environ.get("GOOGLE_API_KEY"))
    if not api_key:
        api_key = st.text_input("Enter your Google API Key:", type="password")
        if not api_key:
            st.warning("Please enter your Google API Key to continue")
            st.stop()
    
    os.environ["GOOGLE_API_KEY"] = api_key
    return genai.Client(api_key=api_key)

# Function to generate image
def generate_image(prompt, client):
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp-image-generation",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=['Text', 'Image']
            )
        )
        
        result = {"image": None, "text": None}
        
        for part in response.candidates[0].content.parts:
            if part.text is not None:
                result["text"] = part.text
            elif part.inline_data is not None:
                image = Image.open(BytesIO(part.inline_data.data))
                result["image"] = image
                
        return result
    except Exception as e:
        st.error(f"Error generating image: {str(e)}")
        return None

# Function to modify image
def modify_image(prompt, image, client):
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp-image-generation",
            contents=[prompt, image],
            config=types.GenerateContentConfig(
                response_modalities=['Text', 'Image']
            )
        )
        
        result = {"image": None, "text": None}
        
        for part in response.candidates[0].content.parts:
            if part.text is not None:
                result["text"] = part.text
            elif part.inline_data is not None:
                image = Image.open(BytesIO(part.inline_data.data))
                result["image"] = image
                
        return result
    except Exception as e:
        st.error(f"Error modifying image: {str(e)}")
        return None

# Main app
def main():
    st.title("Gemini Image Creator")
    
    client = initialize_client()
    
    # Sidebar for navigation
    page = st.sidebar.radio("Choose an Option", ["Generate New Image", "Modify Existing Image"])
    
    if page == "Generate New Image":
        st.header("Generate a New Image")
        
        prompt = st.text_area("Enter your prompt:", 
                            "Create a sketch image template for a drawing of a city in perspective viewpoint", 
                            height=100)
        
        if st.button("Generate Image"):
            with st.spinner("Generating image..."):
                result = generate_image(prompt, client)
                
                if result and result["image"]:
                    st.image(result["image"], caption="Generated Image", use_column_width=True)
                    
                    # Save image option
                    img_buffer = BytesIO()
                    result["image"].save(img_buffer, format="PNG")
                    img_bytes = img_buffer.getvalue()
                    
                    st.download_button(
                        label="Download Image",
                        data=img_bytes,
                        file_name="gemini-generated-image.png",
                        mime="image/png"
                    )
                    
                    # Display any text response
                    if result["text"]:
                        st.text_area("Model Response:", result["text"], height=100)
                    
                    # Store the generated image in session state for modification
                    st.session_state.last_generated_image = result["image"]
    
    else:  # Modify Existing Image
        st.header("Modify an Image")
        
        # Image upload
        uploaded_file = st.file_uploader("Upload an image to modify", type=["png", "jpg", "jpeg"])
        
        # Use the last generated image if available
        use_last_generated = False
        if hasattr(st.session_state, 'last_generated_image'):
            use_last_generated = st.checkbox("Use last generated image", value=True)
        
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Image", use_column_width=True)
        elif use_last_generated:
            image = st.session_state.last_generated_image
            st.image(image, caption="Last Generated Image", use_column_width=True)
        else:
            st.info("Please upload an image or generate one first")
            return
            
        modification_prompt = st.text_area("Enter modification instructions:", 
                                          "Make the buildings taller and add more details", 
                                          height=100)
        
        if st.button("Modify Image"):
            with st.spinner("Modifying image..."):
                result = modify_image(modification_prompt, image, client)
                
                if result and result["image"]:
                    st.image(result["image"], caption="Modified Image", use_column_width=True)
                    
                    # Save image option
                    img_buffer = BytesIO()
                    result["image"].save(img_buffer, format="PNG")
                    img_bytes = img_buffer.getvalue()
                    
                    st.download_button(
                        label="Download Modified Image",
                        data=img_bytes,
                        file_name="gemini-modified-image.png",
                        mime="image/png"
                    )
                    
                    # Display any text response
                    if result["text"]:
                        st.text_area("Model Response:", result["text"], height=100)
                    
                    # Store the modified image in session state
                    st.session_state.last_generated_image = result["image"]

if __name__ == "__main__":
    main()
