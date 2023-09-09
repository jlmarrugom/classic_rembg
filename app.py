import streamlit as st
from utils import download_image, BackgroundRemover, CollageMaker

st.title("Welcome to the RemBG app")

img_url = st.sidebar.text_input("Input the Image Url")
if img_url == "":
    url_options=[
            "https://http2.mlstatic.com/D_NQ_NP_2X_934890-MLU54973030786_042023-F.webp",
            "https://http2.mlstatic.com/D_NQ_NP_2X_838627-MCO44046010851_112020-F.webp",
            "https://http2.mlstatic.com/D_NQ_NP_2X_893800-MCO44046010850_112020-F.webp",
        ]
    img_url = st.sidebar.selectbox("Or, choose one of the following urls:", options=url_options)
if img_url is not "":
    
    img = download_image(img_url)
    st.sidebar.image(img)

    remover =  BackgroundRemover()
    png_image = remover.remove_backgroung(img)
    st.write("### Image Without White Background")
    st.image(png_image)

    st.write("### Collage")
    overlapping = st.sidebar.number_input("Overlapping:", min_value=0.0, max_value=1.0, value=0.3)
    collage_maker = CollageMaker()
    collage = collage_maker.make_collage(png_image, overlapping ,num_repeats=2)
    st.image(remover.make_black_pixels_transparent(collage))

else: st.sidebar.info("Input an URL first")

