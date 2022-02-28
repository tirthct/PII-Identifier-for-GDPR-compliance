
import NLP
import logging.config
import cv2
import pafy
from subprocess import call
import tensorflow as tf
import save_to_file as sf
from models import yolo
from log_config import LOGGING
from utils.general import format_predictions, find_class_by_name, is_url
import os
import glob
from subprocess import call

logging.config.dictConfig(LOGGING)

logger = logging.getLogger('detector')
FLAGS = tf.flags.FLAGS
VALID_IMAGES = [".jpg", ".jpeg", ".gif", ".png", ".tga", ".tif", ".bmp"]
FNULL = open(os.devnull, 'w')


def evaluate(_):
    # print("inside evaluate")
    #
    img_path = r"C:\Users\tirtht\PycharmProjects\DeepDream\yolo_images\test.jpg"
    # img = cv2.imread(img_path)
    # img = cv2.resize(img, (1600, 1200))
    # model_cls = find_class_by_name(FLAGS.model_name, [yolo])
    # model = model_cls(input_shape=(1200, 1600, 3))
    # model.init()
    #
    # predictions = model.evaluate(img)
    # print(predictions)
    # classes = []
    # for o in predictions:
    #     x1 = o['box']['left']
    #     x2 = o['box']['right']
    #
    #     y1 = o['box']['top']
    #     y2 = o['box']['bottom']
    #
    #     color = o['color']
    #     class_name = o['class_name']
    #
    #     # Draw box
    #     cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
    #
    #     # Draw label
    #     (test_width, text_height), baseline = cv2.getTextSize(
    #         class_name, cv2.FONT_HERSHEY_SIMPLEX, 0.75, 1)
    #     cv2.rectangle(img, (x1, y1),
    #                   (x1 + test_width, y1 - text_height - baseline),
    #                   color, thickness=cv2.FILLED)
    #     cv2.putText(img, class_name, (x1, y1 - baseline),
    #                 cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 0), 1)
    #     classes.append(class_name)
    # sf.save("frame", classes)
    # cv2.imshow("detector", img)
    #
    # cv2.imwrite(r"C:\Users\tirtht\PycharmProjects\DeepDream\yolo_images\\" +img_path.split("\\")[-1],img)
    # cv2.waitKey(1)
    # cv2.destroyAllWindows()
    # # fname = file.split("\\")[-1]
    # # print(fname.split(".")[0])
    # # text_file_path = os.path.join(r"C:\Users\neelp\PycharmProjects\devicehive-video-analysis\Output", fname.split(".")[0])
    # # print("text-file-path"+text_file_path)
    call(["tesseract", img_path, r"C:\Users\tirtht\PycharmProjects\DeepDream\ocr"], stdout=FNULL)
    #
    # # NLP.extract_names_from_text(text_file_path+".txt")
    # model.close()


if __name__ == '__main__':
    # tf.flags.DEFINE_string('video', 0, 'Path to the video file.')
    tf.flags.DEFINE_string('model_name', 'Yolo2Model', 'Model name to use.')

    tf.app.run(main=evaluate)
