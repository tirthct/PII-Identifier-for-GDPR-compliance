# ======== IMPORTS ========

import os
from io import BytesIO
import numpy as np
from functools import partial
import PIL.Image
import tensorflow as tf
import face_recognition
from PIL import Image
#from video import eval_img
import glob
import eval_img


# =========================

# ======== SETUP ========

"""
The GoogLeNet architecture (InceptionV5) is used here which has been pretrained on multiple for several weeks on the
ImageNet dataset.
"""

# Model location
model_fn = "tensorflow_inception_graph.pb"

# Create an interactive session and base to load the graph into
graph = tf.Graph()
sess = tf.InteractiveSession(graph=graph)

# Read the graph in
with tf.gfile.FastGFile(model_fn, "rb") as f:
    graph_def = tf.GraphDef()
    graph_def.ParseFromString(f.read())

# Define the input Tensor
t_input = tf.placeholder(np.float32, name="input")
imagenet_mean = 117.0
t_preprocessed = tf.expand_dims(t_input - imagenet_mean, 0)
tf.import_graph_def(graph_def, {"input":t_preprocessed})

# Variables needed for the Laplacian pyramid construction
k = np.float32([1, 4, 6, 4, 1])
k = np.outer(k, k)
k5x5 = k[:, :, None, None] / k.sum() * np.eye(3, dtype=np.float32)

# =======================

# ======== HELPER FUNCTIONS ========

def showarray(a, octave,fmt="jpeg"):
    a = np.uint8(np.clip(a, 0, 1) * 255)
    img = PIL.Image.fromarray(a)
    if(octave==1):
        img.save("fuzzy.jpg")
        print("fuzzy image saved!")
    img.show()

def wait():
    input("Press enter to continue...")

def visstd(a, s=0.1):
    """
    Normalise the image range for visualisation.
    :param a: the array to normalise
    :param s: ?
    :return: the normalised image
    """
    return (a - a.mean()) / max(a.std(), 1e-4)*s + 0.5

def T(layer):
    """
    Convenience function for getting a layer's output tensor
    :param layer: the layer to get the tensor
    :return: the tensor
    """
    return graph.get_tensor_by_name("import/%s:0" % layer)

def lap_split(img):
    """
    Splits the image into high and low frequency images
    :param img: the image to split
    :return: a tuple of the low and high frequency components of the image
    """
    with tf.name_scope("split"):
        lo = tf.nn.conv2d(img, k5x5, [1, 2, 2, 1], "SAME")
        lo2 = tf.nn.conv2d_transpose(lo, k5x5*4, tf.shape(img), [1, 2, 2, 1])
        hi = img - lo2

    return lo, hi

def lap_split_n(img, n):
    """
    Build the laplacian pyramid with n splits.
    :param img: image to split
    :param n: number of splits
    :return: the laplacian pyramid
    """
    levels = []

    for i in range(n):
        img, hi = lap_split(img)
        levels.append(hi)

    levels.append(img)
    return levels[::-1]

def lap_merge(levels):
    """
    Merge the laplacian pyramid.
    :param levels: list of the different images in the pyramid (each image is a level).
    :return: the image from the laplacian pyramid.
    """
    img = levels[0]

    for hi in levels[1:]:
        with tf.name_scope("merge"):
            img = tf.nn.conv2d_transpose(img, k5x5*4, tf.shape(hi), [1, 2, 2, 1]) + hi

    return img

def normalize_std(img, eps=1e-10):
    """
    Normalise the image by making its standard deviation equal to 1.
    :param img: the image to normalise.
    :param eps: to ensure no division by zero.
    :return: the normalised image
    """
    with tf.name_scope("normalize"):
        std = tf.sqrt(tf.reduce_mean(tf.square(img)))
        return img / tf.maximum(std, eps)

def lap_normalize(img, scale_n=4):
    """
    Performs Laplacian pyramid normalisation.
    :param img: image to normalise.
    :param scale_n: number of levels in the pyramid
    :return: the Laplacian pyramid normalized image
    """
    img = tf.expand_dims(img, 0)
    tlevels = lap_split_n(img, scale_n)
    tlevels = list(map(normalize_std, tlevels))
    out = lap_merge(tlevels)
    return out[0, :, :, :]

def tffunc(*argtypes):
    """
    Helper function that transforms the TF-graph generating function into a regular one - used to resize the image with
    Tensorflow in combination with the "resize" function below.
    :param argtypes: multiple parameters.
    :return: a normal function
    """
    placeholders = list(map(tf.placeholder, argtypes))

    def wrap(f):
        out = f(*placeholders)

        def wrapper(*args, **kw):
            return out.eval(dict(zip(placeholders, args)), session=kw.get("session"))

        return wrapper

    return wrap

def resize(img, size):
    """
    Resizes and image using Tensorflow. Works in tandem with tffunc, above.
    :param img: the image to resize.
    :param size: the size to change the image to.
    :return: the resized image.
    """
    # Adds an extra dimension to the image at index 1, for example we already have img=[height, width, channels], then
    # by using "expand_dims" we turn this into a batch of 1 images: [1, height, width, channels].
    img = tf.expand_dims(img, 0)

    return tf.image.resize_bilinear(img, size)[0, :, :, :]

# Wrap the TF-based resize function to make it into a normally callable function
resize = tffunc(np.float32, np.int32)(resize)

def calc_grad_tiled(img, t_grad, tile_size=512):
    """
    Computes the value of tensor t_grad over the image in a tiled way. Random shifts are applied to the image to blur
    tile boundaries over multiple iterations.
    :param img: the image to modify.
    :param t_grad: the gradient to compute, as a TensorFlow operation.
    :param tile_size: the size of each image tile.
    :return: the randomly shifted image.
    """
    # Image metrics
    size = tile_size
    height, width = img.shape[:2]

    # Random shift coordinates
    sx, sy = np.random.randint(size, size=2)

    # Shift the image
    img_shift = np.roll(np.roll(img, sx, 1), sy, 0)

    # The gradient of the image
    grad = np.zeros_like(img)

    # Calculate the gradients for the image tiles. These funky for loop conditions are for if the image is larger than
    # the size of each tile. If it's smaller than the tile, we can compute it all in one. If it's larger than the tile,
    # then we will have to do multiple iterations to discover the gradient for the whole image.
    for y in range(0, max(height-size//2, size), size):
        for x in range(0, max(width-size//2, size), size):

            sub = img_shift[y:y+size, x:x+size]
            g = sess.run(t_grad, {t_input: sub})
            grad[y:y+size, x:x+size] = g

    return np.roll(np.roll(grad, -sx, 1), -sy, 0)

def render_deepdream(t_obj, img0, iter_n=100, step=1.5, octave_n=3, ocatve_scale=1.4):
    """
    Render in DeepDream style.
    :param t_obj: the objective to enhance.
    :param img0: the image to enhance.
    :param iter_n: number of iterations.
    :param step: number of steps.
    :param octave_n: number of octaves.
    :param ocatve_scale: scale to increase image size by each time.
    """

    # Optimisation objective
    t_score = tf.reduce_mean(t_obj)

    # Gradient
    t_grad = tf.gradients(t_score, t_input)[0]

    # Split the image into a number of octaves
    img = img0
    octaves = []
    for i in range(octave_n-1):
        print(i)
        hw = img.shape[:2]
        lo = resize(img, np.int32(np.float32(hw)/ocatve_scale))
        hi = img-resize(lo, hw)
        img = lo
        octaves.append(hi)

    # Generate details octave by octave
    for octave in range(octave_n):
        print("Octave is "+octave.__str__())
        if octave > 0:
            hi = octaves[-octave]
            img = resize(img, hi.shape[:2]) + hi

        for i in range(iter_n):
            print("Iteration :",i)
            g = calc_grad_tiled(img, t_grad)
            img += g * (step / (np.abs(g).mean()+1e-7))

            print(".", end=" ")

        showarray(img/255.0,octave)

# ==================================

# ======== MAIN CODE ========

"""
We try to generate images that maximize the sum of activations of a a particular channel of a particular convolutional
layer of the neural network. InceptionV5 contains many convolutional layers, each of which outputs tens to hundreds of
feature channels. This allows many different patterns to be explored.
"""

# Create a list of all the layers in the network
layers = [op.name for op in graph.get_operations() if op.type=="Conv2D" and "import/" in op.name]
feature_nums = [int(graph.get_tensor_by_name(name+":0").get_shape()[-1]) for name in layers]

"""
LAPLACIAN_PYRAMID_DREAMING adds a "smoothness prior" to the optimization objective, so that high image frequencies are
more muted and low frequencies will become more apparent. A Laplacian pyramid is used to provide this smoothing for
images of different sizes.
"""

# Pick an internal layer to enhance. We use outputs before applying the ReLU nonlinearity to have non-zero gradients
# for features with negative initial activations
layer_i = "mixed4d_3x3_bottleneck_pre_relu"
layer_ii = "mixed3b_1x1_pre_relu"
layer_iii = "mixed4c"

# Pick a random feature channel to visualise - there are 144 in that layer
channel_i = 143
channel_ii = 50
channel_iii = 1

# Make an image of random noise
img_noise = np.random.uniform(size=(224, 224, 3)) + 100.0

# Read an image - applying simple dreaming to it doesn't really do anything just overlays the same pattern as random
# noise but very vaguely

#for picture in os.listdir(r'C:\images'):
#    print('image '+picture)
#    image = PIL.Image.open('C:\\images\\'+picture)
#    image = np.float32(image)
folder=glob.glob(r'C:\New folder\*')
for file in folder:
    fname=file.split("\\")[-1]
    image=PIL.Image.open(file)
    print("Image is ",file)
    #image=image.resize((800,600))
    image= image.convert('RGB')
    image.save("resizedImage.jpg")
    image=PIL.Image.open("resizedImage.jpg")
    image=np.float32(image)

    print("Image resized...\nNow deep dreaming")


# The objective to visualise
#objective = T(layer_i)[:, :, :, channel_i] + T(layer_i)[:, :, :, channel_ii] + T(layer_i)[:, :, :, channel_iii]
    objective = tf.square(T(layer_i))

# Render the image
    render_deepdream(objective, img0=image, octave_n=2)


#face detection in original image

    org_image=face_recognition.load_image_file("resizedImage.jpg")

    face_locations = face_recognition.face_locations(org_image)

    i = 0

    print('Total found faces are', len(face_locations))



    for face_location in face_locations:


        # Print the location of each face in this image

        top, right, bottom, left = face_location

        print("A face is located at pixel location Top: {}, Left: {}, Bottom: {}, Right: {}".format(top, left, bottom,

                                                                                                    right))

        obfuscated_image=Image.open('fuzzy.jpg')

        cropped_obfuscated_image=obfuscated_image.crop((left,top,right,bottom))


    #original_image=image.copy()

    #original_image.save("tempimage.jpg")
        if(i==0):
            temporary_image=Image.open("resizedImage.jpg")
        else:
            temporary_image=Image.open('obfuscated_images\\'+fname)

        temporary_image.paste(cropped_obfuscated_image, (left, top, right, bottom))
        temporary_image.save('obfuscated_images\\'+fname)

        print("Face obfuscated")
        i=i+1

# eval_img.evaluate()

