import streamlit as st
from utils import download_image, BackgroundRemover, CollageMaker

st.title("Welcome to the RemBG app")

img_url = st.sidebar.text_input("Input the Image Url")
url_options=[
        "https://http2.mlstatic.com/D_NQ_NP_2X_934890-MLU54973030786_042023-F.webp",
        "https://http2.mlstatic.com/D_NQ_NP_2X_838627-MCO44046010851_112020-F.webp",
        "https://http2.mlstatic.com/D_NQ_NP_2X_893800-MCO44046010850_112020-F.webp",
        "https://http2.mlstatic.com/D_NQ_NP_2X_707713-MLC47514320566_092021-F.webp"
    ]
with st.sidebar.expander("Example URLs"):
    for url in url_options:
        st.write(url)

overlapping = st.sidebar.number_input("Overlapping:", min_value=0.0, max_value=1.0, value=0.3)
nr = st.sidebar.number_input("Number of repeats:", min_value=2, max_value=6, value=2)

c1, c2 = st.columns([2,3], gap="large")
if img_url != "":
    
    img = download_image(img_url)

    remover =  BackgroundRemover()
    png_image = remover.remove_backgroung(img)
    with c1:
        st.write("### Image Without White Background")
        st.image(png_image)

    collage_maker = CollageMaker()
    collage = collage_maker.make_collage(png_image, overlapping ,num_repeats=nr)
    with c2:
        st.write("### Collage")
        st.image(collage)

else: st.sidebar.info("Input an URL first")

