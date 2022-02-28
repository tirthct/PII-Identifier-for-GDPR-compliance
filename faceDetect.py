from PIL import Image, ImageDraw
import cv2
import face_recognition
image = face_recognition.load_image_file(r"C:\New folder\test1.jpg")
face_locations = face_recognition.face_locations(image)
for face_location in face_locations:
    # Print the location of each face in this image

    top, right, bottom, left = face_location
    im = cv2.imread(r'C:\New folder\test1.jpg')
    row, col = im.shape[:2]
    bottom = im[row - 2:row, 0:col]
    mean = cv2.mean(bottom)[0]

    bordersize = 10
    border = cv2.copyMakeBorder(im, top=top, bottom=bottom, left=left, right=right,
                                borderType=cv2.BORDER_CONSTANT, value=[mean, mean, mean])

    cv2.imshow('image', im)
    cv2.imshow('bottom', bottom)
    cv2.imshow('border', border)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
