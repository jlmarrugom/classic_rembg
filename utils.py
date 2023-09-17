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

    def remove_backgroung(self, opencvImage:np.ndarray)-> np.ndarray:
        """Run the full background removal process"""
        gray_img = cv2.cvtColor(opencvImage, cv2.COLOR_BGR2GRAY)
        opencvImage = cv2.add(opencvImage, 1)

        contours, cnt_border = self.find_contours(gray_img)

        mask = self.find_mask(gray_img, contours)

        masked_img = cv2.bitwise_and(opencvImage, opencvImage, mask=mask)

        masked_img = self.crop_image_by_max_contours(masked_img, cnt_border)

        png_img = self.make_pixels_transparent(masked_img, objective="black")

        return png_img

    @staticmethod
    def find_contours(gray_img:np.ndarray)->np.ndarray:
        """Find the contours of the image"""
        _, threshed = cv2.threshold(gray_img, 230, 255, cv2.THRESH_BINARY_INV) #220

        ## (2) Morph-op to remove noise
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2,2)) #11,11
        morphed = cv2.morphologyEx(threshed, cv2.MORPH_CLOSE, kernel, iterations=1)

        ## (3) Find the max-area contour
        contours = cv2.findContours(morphed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]

        cnt = sorted(contours, key=cv2.contourArea)[-1]

        return contours, cnt
    
    @staticmethod
    def crop_image_by_max_contours(image:np.ndarray, cnt:np.ndarray)->np.ndarray:
        """Crop Image by contours"""
        x,y,w,h = cv2.boundingRect(cnt)
        minimal_border_img = image[y:y+h, x:x+w]

        return minimal_border_img

    @staticmethod
    def find_mask(gray_img:np.ndarray, contours:np.ndarray)->np.ndarray:
        """Find an inclusive mask of the image with the countours then fills it"""
        tmp = np.zeros_like(gray_img)
        filled_boundary = cv2.drawContours(tmp, contours, -1, (255,255,255), thickness=cv2.FILLED)# with 1 just draw the countour
        filled_boundary[filled_boundary > 0] = 255
        return filled_boundary
    
    @staticmethod
    def make_pixels_transparent(image_bgr:np.ndarray, objective:str="white")->np.ndarray:
        """Make the objective Pixels transparent by adding another channel"""
        # get the image dimensions (height, width and channels)
        h, w, c = image_bgr.shape
        # append Alpha channel -- required for BGRA (Blue, Green, Red, Alpha)
        image_bgra = np.concatenate([image_bgr, np.full((h, w, 1), 255, dtype=np.uint8)], axis=-1)
        # create a mask where white pixels ([255, 255, 255]) are True
        if objective=="white":
            white = np.all(image_bgr == [255, 255, 255], axis=-1)
            # change the values of Alpha to 0 for all the white pixels
            image_bgra[white, -1] = 0
        else:
            black = np.all(image_bgr == [0, 0, 0], axis=-1)
            # change the values of Alpha to 0 for all the black pixels
            image_bgra[black, -1] = 0

        return image_bgra

class CollageMaker:

    def make_collage(self, img_list:list, overlapping:float=0.3)->np.ndarray:
        """Make a collage with a list of images and the desired overlapping"""
        padded_list = self.add_border_to_images(img_list, overlapping=overlapping)
        # if right equals front:
        current_collage = padded_list[-1]
        for img in padded_list[::-1][1:]:
            current_collage = self.blend_two_images(front_img=current_collage, back_image=img[:,:,:3])
            bgrm = BackgroundRemover()
            current_collage = bgrm.make_pixels_transparent(current_collage, objective="black")
        #collage = self.blend_two_images(front_img=padded_list[-1], back_image=padded_list[0])

        return current_collage
    
    @staticmethod
    def add_border_to_images(img_list:list, overlapping:float = 0.3)->list:
        """Pad the images in the list depending on the desired overlapping and their shapes"""
        x_offset = round((1-overlapping) *img_list[0].shape[1])
        # add borders
        new_imgs = len(img_list)*[None]
        borderType=cv2.BORDER_CONSTANT
        for i, img in enumerate(img_list):
            
            # left_offset = sum(
            #     [round(left_img.shape[1]-overlapping *img.shape[1]) for left_img in img_list[:i]]
            #     )
            # right_offset = sum(
            #     [round((1-overlapping) *right_img.shape[1]) for right_img in img_list[i:]])

            new_imgs[i] = cv2.copyMakeBorder(
                img,
                top= 0, 
                bottom=0,
                left=i*x_offset, #left_offset,
                right= (len(img_list)-1-i)*x_offset, #right_offset
                borderType=borderType
                )

        return new_imgs
    
    @staticmethod
    def blend_two_images(front_img:np.ndarray, back_image:np.ndarray)->np.ndarray:
        """Put two images together, one in the front and one in the back"""
        # extract alpha channel from foreground image as mask and make 3 channels
        alpha = front_img[:,:,3]
        alpha = cv2.merge([alpha,alpha,alpha])

        # extract bgr channels from foreground image
        front = front_img[:,:,0:3]
        back = back_image[:,:,0:3]

        # blend the two images using the alpha channel as controlling mask
        blended_img = np.where(alpha==(0,0,0), back, front)

        return blended_img