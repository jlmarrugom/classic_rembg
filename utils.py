import cv2
import numpy as np

from PIL import Image
import requests
from io import BytesIO

def download_image(url:str)->np.ndarray:
    """Download an image from the given URL"""
    response = requests.get(url)
    img = Image.open(BytesIO(response.content))
    opencvImage = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    return opencvImage

class BackgroundRemover:
    """This is a wrapper class with Image preprocess methods"""

    def remove_backgroung(self, opencvImage:np.ndarray)-> None:
        """Run the full background removal process"""
        gray_img = cv2.cvtColor(opencvImage, cv2.COLOR_BGR2GRAY)

        contours, cnt_border = self.find_contours(gray_img)

        mask = self.find_mask(gray_img, contours)

        masked_img = cv2.bitwise_and(opencvImage, opencvImage, mask=mask)

        masked_img = self.crop_image_by_max_contours(masked_img, cnt_border)

        png_img = self.make_black_pixels_transparent(masked_img)

        return png_img

    @staticmethod
    def find_contours(gray_img):
        """Find the contours of the image"""
        _, threshed = cv2.threshold(gray_img, 220, 255, cv2.THRESH_BINARY_INV)

        ## (2) Morph-op to remove noise
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11,11))
        morphed = cv2.morphologyEx(threshed, cv2.MORPH_CLOSE, kernel)

        ## (3) Find the max-area contour
        contours = cv2.findContours(morphed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
        cnt = sorted(contours, key=cv2.contourArea)[-1]

        return contours, cnt
    
    @staticmethod
    def crop_image_by_max_contours(image, cnt):
        ## (4) Crop and save it
        x,y,w,h = cv2.boundingRect(cnt)
        minimal_border_img = image[y:y+h, x:x+w]

        return minimal_border_img

    @staticmethod
    def find_mask(gray_img, contours)->np.ndarray:
        """Find an inclusive mask of the image with the countours then fills it"""
        tmp = np.zeros_like(gray_img)
        filled_boundary = cv2.drawContours(tmp, contours, -1, (255,255,255), thickness=cv2.FILLED)# with 1 just draw the countour
        filled_boundary[filled_boundary > 0] = 255
        return filled_boundary
    
    @staticmethod
    def make_black_pixels_transparent(image_bgr:np.ndarray)->np.ndarray:

        # get the image dimensions (height, width and channels)
        h, w, c = image_bgr.shape
        # append Alpha channel -- required for BGRA (Blue, Green, Red, Alpha)
        image_bgra = np.concatenate([image_bgr, np.full((h, w, 1), 255, dtype=np.uint8)], axis=-1)
        # create a mask where white pixels ([255, 255, 255]) are True
        #white = np.all(image_bgr == [255, 255, 255], axis=-1)
        black = np.all(image_bgr == [0, 0, 0], axis=-1)
        # change the values of Alpha to 0 for all the black pixels
        image_bgra[black, -1] = 0

        return image_bgra

class CollageMaker:

    def make_collage(self, img, overlapping=0.3, num_repeats=2):

        img_list = num_repeats*[img]
        padded_list = self.add_border_to_images(img_list, overlapping=overlapping)
        collage = self.blend_two_images(front_img=padded_list[-1], back_image=padded_list[0])

        return collage
    
    @staticmethod
    def add_border_to_images(img_list, overlapping:float = 0.3):
        # function as a pair
        x_offset=round((1-overlapping)*img_list[0].shape[1])
        # add borders
        new_imgs = len(img_list)*[None]
        borderType=cv2.BORDER_CONSTANT
        for i, img in enumerate(img_list):
            new_imgs[i] = cv2.copyMakeBorder(
                img,
                top= 0, 
                bottom=0,
                left= i*x_offset, 
                right=(len(img_list)-1-i)*x_offset,
                borderType=borderType
                )

        return new_imgs
    
    @staticmethod
    def blend_two_images(front_img, back_image):
        # extract alpha channel from foreground image as mask and make 3 channels
        alpha = front_img[:,:,3]
        alpha = cv2.merge([alpha,alpha,alpha])

        # extract bgr channels from foreground image
        front = front_img[:,:,0:3]
        back = back_image[:,:,0:3]

        # blend the two images using the alpha channel as controlling mask
        blended_img = np.where(alpha==(0,0,0), back, front)

        return blended_img