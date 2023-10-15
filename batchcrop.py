import sys
import os
import cv2
import numpy as np
import keyboard
import configparser

MAX_WIDTH = 900
MAX_HEIGHT = 700
WINDOW_NAME = "preview"
ORIENTATION_AUTO = 0
ORIENTATION_LANDSCAPE = 1
ORIENTATION_PORTRAIT = 2
LEFT_ARROW = 0x250000
UP_ARROW = 0x260000
RIGHT_ARROW = 0x270000
DOWN_ARROW = 0x280000
EXIT_KEY = ord("q")
SKIP_KEY = ord("s")
SAVE_KEY = 32
FORCE_PORTRAIT_KEY = ord("p")
FORCE_LANDSCAPE_KEY = ord("l")

IMG_FOLDER = r"images"
CROPPED_FOLDER = r"cropped"
ASPECT_RATIO = 15 / 10


def load_config():
    global IMG_FOLDER, CROPPED_FOLDER, ASPECT_RATIO
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(__file__)
    config_name = "config.ini"
    config_path = os.path.join(application_path, config_name)
    config = configparser.ConfigParser()
    if os.path.exists(config_path):
        config.read(config_path)
        settings = config["Settings"]
        IMG_FOLDER = settings["ImagesPath"]
        CROPPED_FOLDER = settings["CroppedPath"]
        ASPECT_RATIO = float(settings["AspectRatio"])
        if os.path.exists(IMG_FOLDER) and os.path.exists(CROPPED_FOLDER):
            return True
    else:
        IMG_FOLDER = os.path.join(application_path, "images")
        CROPPED_FOLDER = os.path.join(application_path, "cropped")
        config["Settings"] = {"ImagesPath": IMG_FOLDER,
                              "CroppedPath": CROPPED_FOLDER,
                              "AspectRatio": ASPECT_RATIO}
        with open(config_path, "w") as config_file:
            config.write(config_file)
    return False


def get_image_files(folder):
    valid_extensions = [".jpg", ".png"]
    file_list = [os.path.join(folder, x) for x in os.listdir(folder)]
    return [file_path for file_path in file_list if
            os.path.isfile(file_path) and os.path.splitext(file_path)[1] in valid_extensions]


def get_file_name(file_path):
    return os.path.splitext(os.path.basename(file_path))[0]


def get_files_to_process():
    image_files = get_image_files(IMG_FOLDER)
    cropped_files = get_image_files(CROPPED_FOLDER)
    cropped_names = [get_file_name(x) for x in cropped_files]
    return [file_path for file_path in image_files if get_file_name(file_path) not in cropped_names]


def get_cropped_size(img_size, orientation):
    crop_width, crop_height = img_width, img_height = img_size
    if orientation == ORIENTATION_AUTO:
        orientation = ORIENTATION_LANDSCAPE if img_width > img_height else ORIENTATION_PORTRAIT
    aspect_ratio = ASPECT_RATIO if orientation == ORIENTATION_LANDSCAPE else 1 / ASPECT_RATIO
    max_width = int(img_height * aspect_ratio)
    max_height = int(img_width / aspect_ratio)
    if img_width > max_width:
        crop_width = max_width
    elif img_height > max_height:
        crop_height = max_height
    return crop_width, crop_height


def has_correct_aspect_ratio(img_size, cropped_size):
    error_width = abs((cropped_size[0] / img_size[0]) - 1)
    error_height = abs((cropped_size[1] / img_size[1]) - 1)
    return error_width <= 0.01 and error_height <= 0.01


def get_center_offset(img_size, cropped_size):
    return ((img_size[0] - cropped_size[0]) // 2,
            (img_size[1] - cropped_size[1]) // 2)


def add_tuple(a, b):
    return a[0] + b[0], a[1] + b[1]


def scale_tuple(x, scaling_factor):
    return int(x[0] * scaling_factor), int(x[1] * scaling_factor)


def get_img_offsets(img_size):
    reference_value = max(img_size[0], img_size[1])
    large_offset = reference_value // 100
    small_offset = reference_value // 500
    return large_offset, small_offset


def get_snapped_offset(key, img_size, cropped_size):
    if key == RIGHT_ARROW:
        return (img_size[0] - cropped_size[0]), 0
    elif key == LEFT_ARROW or key == UP_ARROW:
        return 0, 0
    elif key == DOWN_ARROW:
        return 0, (img_size[1] - cropped_size[1])


def get_move_offset(key, img_offsets):
    offset = img_offsets[0] if keyboard.is_pressed("ctrl") else img_offsets[1]
    if key == RIGHT_ARROW:
        return offset, 0
    elif key == LEFT_ARROW:
        return -offset, 0
    elif key == UP_ARROW:
        return 0, -offset
    elif key == DOWN_ARROW:
        return 0, offset


def check_offset_boundaries(img_size, cropped_size, rect_offset):
    return (max(0, min(rect_offset[0], img_size[0] - cropped_size[0])),
            max(0, min(rect_offset[1], img_size[1] - cropped_size[1])))


def save_cropped_image(img, cropped_size, rect_offset, file_path):
    start_index = rect_offset
    end_index = add_tuple(rect_offset, cropped_size)
    img_cropped = img[start_index[1]:end_index[1], start_index[0]:end_index[0]]
    name = os.path.basename(os.path.splitext(file_path)[0])
    cropped_name = os.path.join(CROPPED_FOLDER, name + ".jpg")
    cv2.imwrite(cropped_name, img_cropped, [cv2.IMWRITE_JPEG_QUALITY, 95])


def draw_rectangle(img_preview, start_point, end_point):
    mask = 255 * np.ones_like(img_preview)
    cv2.rectangle(mask, start_point, end_point, (0, 0, 0), -1)
    img = cv2.scaleAdd(mask, -0.3, img_preview)
    cv2.rectangle(img, start_point, end_point, (20, 20, 20), 2)
    cv2.rectangle(img, start_point, end_point, (255, 255, 255), 1)
    return img


def process_files():
    quit_flag = False
    file_list = get_files_to_process()
    cv2.namedWindow(WINDOW_NAME)

    for index, file_path in enumerate(file_list, start=1):
        img = cv2.imread(file_path, cv2.IMREAD_ANYCOLOR)
        img_size = (img.shape[1], img.shape[0])
        cropped_size = get_cropped_size(img_size, ORIENTATION_AUTO)

        # skip if the image already has the correct aspect ratio
        if has_correct_aspect_ratio(img_size, cropped_size):
            save_cropped_image(img, img_size, (0, 0), file_path)
            continue
        rect_offset = get_center_offset(img_size, cropped_size)
        img_offsets = get_img_offsets(img_size)
        scaling_factor = min(MAX_WIDTH / img_size[0], MAX_HEIGHT / img_size[1])
        img_preview = cv2.resize(img, (0, 0), fx=scaling_factor, fy=scaling_factor, interpolation=cv2.INTER_AREA)
        cv2.setWindowTitle(WINDOW_NAME, f"Cropping {index}/{len(file_list)}")

        while True:
            start_point = scale_tuple(rect_offset, scaling_factor)
            end_point = add_tuple(scale_tuple(cropped_size, scaling_factor),
                                  scale_tuple(rect_offset, scaling_factor))
            img_preview_rect = draw_rectangle(img_preview, start_point, end_point)
            cv2.imshow(WINDOW_NAME, img_preview_rect)

            key = cv2.waitKeyEx(0)
            if key == EXIT_KEY:
                quit_flag = True
                break
            if key == SAVE_KEY:
                save_cropped_image(img, cropped_size, rect_offset, file_path)
                break
            if key == SKIP_KEY:
                break
            elif key == RIGHT_ARROW or key == LEFT_ARROW or key == UP_ARROW or key == DOWN_ARROW:
                if keyboard.is_pressed('shift'):
                    rect_offset = get_snapped_offset(key, img_size, cropped_size)
                else:
                    offset = get_move_offset(key, img_offsets)
                    new_offset = add_tuple(rect_offset, offset)
                    rect_offset = check_offset_boundaries(img_size, cropped_size, new_offset)
            elif key == FORCE_PORTRAIT_KEY:
                cropped_size = get_cropped_size(img_size, ORIENTATION_PORTRAIT)
                rect_offset = get_center_offset(img_size, cropped_size)
            elif key == FORCE_LANDSCAPE_KEY:
                cropped_size = get_cropped_size(img_size, ORIENTATION_LANDSCAPE)
                rect_offset = get_center_offset(img_size, cropped_size)
        if quit_flag:
            break
    cv2.destroyAllWindows()


if load_config():
    process_files()
else:
    print("Please edit the config file with the proper paths and try again")
