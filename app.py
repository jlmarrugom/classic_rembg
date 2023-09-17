import streamlit as st
from time import time
from utils import download_image, BackgroundRemover, CollageMaker
from data import url_options

st.title("Welcome to the RemBG app")

img_url = st.sidebar.text_input("Input the Image Url")

with st.sidebar.expander("Example URLs"):
    for url in url_options:
        st.write(url)

overlapping = st.sidebar.number_input("Overlapping:", min_value=0.0, max_value=1.0, value=0.3)
nr = st.sidebar.number_input("Number of repeats:", min_value=1, max_value=6, value=2)

with st.sidebar.expander("Input more URLs"):
    nruls = 2
    extra_urls = nruls*[""]
    extra_nrs = nruls*[None]
    for i in range(nruls):
        extra_urls[i] = st.text_input(f"Input the URL {i}:")
        extra_nrs[i] = st.number_input(f"Number of repeats {i}:", min_value=1, max_value=2, value=1)

st.write("### Images Without White Background")
cols = st.columns(3, gap="large")
all_urls = ([img_url] + extra_urls)
all_nrs = ([nr]+ extra_nrs)
png_images = []
for i, (url, nr) in enumerate(zip(all_urls,all_nrs)):

    if url != "":
        
        img = download_image(url)

        remover =  BackgroundRemover()
        png_image = remover.remove_backgroung(img)
        with cols[i]:
            st.image(png_image, width=130)
        
        png_images+= nr*[png_image]

    else: st.sidebar.info("Input an URL first")


collage_maker = CollageMaker()
collage = collage_maker.make_collage(png_images, overlapping)

st.write("### Collage")
st.image(collage)

