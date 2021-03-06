import os
import matplotlib.pyplot as plt
import numpy as np
import glob

from scipy.stats import mode
from PIL import Image, ImageFilter

PATH_SAVE = 'data/clean/'

PATH_TRAIN_GENUINE = 'data/clean/train-dutch-offline-genuine.npy'
PATH_TRAIN_FORGERIES = 'data/clean/train-dutch-offline-forgeries.npy'


def preprocess_image(image, final_res=256, padding=False, plot=False):
    """ Pre-process a single image.

    The input should be an Image object and the output is a numpy array.

    If `padding` is set to true, the image is padded to be a square before being
    resized to a square of lower resolution (default 256x256 px)

    If `plot` is set, a plot of the images after each step of the pre-processing
    pipeline will be generated
    """

    # Keep track of changes
    images = [('original', image, None)]

    # Convert to gray scale
    image = image.convert('L')
    images.append(('gray scale', image, 'gray'))

    # Find the mode (background color) and convert to black and white with a
    # threshold based on it.
    threshold = int(0.90 * mode(image.getdata())[0][0])
    lut = [0] * threshold + [255] * (256 - threshold)
    image = image.point(lut)
    images.append(('black & white', image, 'gray'))

    # Add padding to form a square if option is set
    if padding:
        image = pad_image_square_center(image)
        images.append(('padding', image, 'gray'))

    # Resize with bilinear interpolation (best results)
    image = image.resize((final_res, final_res), Image.BILINEAR)
    images.append(('resize', image, 'gray'))

    # Plot images if option is set
    if plot:
        fig = plt.figure()
        fig.tight_layout()
        n = len(images)
        for i, (title, im, cmap) in enumerate(images):
            ax = plt.subplot(1, n, i+1)
            ax.set_title(title)
            ax.imshow(im, cmap)
        plt.show()

    # Convert to numpy array
    return np.array(image.getdata()).reshape((final_res, final_res)) / 255


def pad_image_square_center(image):
    """ Pads the given image so that the original is centered on a square.
    """
    new_size = max(image.size)
    new_image = Image.new(image.mode, (new_size, new_size), 'white')
    position = ((new_size - image.size[0]) // 2,
                (new_size - image.size[1]) // 2)
    new_image.paste(image, position)
    return new_image


def fetch_all_raw_genuine():
    """ Returns a list of all the genuine signature files from the raw data.
    That includes the train and test files.s
    """

    # Create list for training set
    path = 'data/raw/trainingSet/OfflineSignatures/Dutch/TrainingSet/' \
           'Offline Genuine/'
    files = glob.glob(path + '*.PNG')

    # Create list for test set
    path = 'data/raw/Testdata_SigComp2011/SigComp11-Offlinetestset/Dutch/' \
           'Reference(646)/'
    files += glob.glob(path + '**/*.*', recursive=True)
    path = 'data/raw/Testdata_SigComp2011/SigComp11-Offlinetestset/Dutch/' \
           'Questioned(1287)/'
    files += glob.glob(path + '**/*_' + '[0-9]' * 3 + '.*', recursive=True)
    return files


def fetch_all_raw_forgeries():
    """ Returns a list of all the forged signature files from the raw data.
    That includes the train and test files.
    """

    # Create list for training set
    path = 'data/raw/trainingSet/OfflineSignatures/Dutch/TrainingSet/' \
           'Offline Forgeries/'
    files = glob.glob(path + '*.png')

    # Create list for test set
    path = 'data/raw/Testdata_SigComp2011/SigComp11-Offlinetestset/Dutch/' \
           'Questioned(1287)/'
    files += glob.glob(path + '**/*_' + '[0-9]'*7 + '.*', recursive=True)
    return files


def batch_preprocess(files_list, dest_file, final_res, padding):
    """ Executes the pre-processing pipeline on all images listed in the given
    files list. The dataset of pre-processed images are saved as a numpy array
    to the given destination file.

    The source folder should not contain any other files apart from the images
    to pre-process. The folder name should be of the form 'path/to/folder/'.
    """

    num_files = len(files_list)
    dataset = np.empty((num_files, final_res*final_res))
    for row, file in enumerate(files_list):
        print('\r{}/{}'.format(row+1, num_files), end='')
        im = Image.open(file)
        im = preprocess_image(im, final_res, padding)
        dataset[row] = im.reshape((1, -1))

    if not os.path.exists(PATH_SAVE):
        os.makedirs(PATH_SAVE)

    np.save(dest_file, dataset)
    print(' - Done!')


if __name__ == '__main__':

    final_res = 128
    padding = True

    # Offline genuine
    files_list = fetch_all_raw_genuine()
    n_sig = len(files_list)
    batch_preprocess(
        files_list,
        PATH_TRAIN_GENUINE,
        final_res,
        padding)

    # Offline forgeries
    files_list = fetch_all_raw_forgeries()
    n_sig += len(files_list)
    batch_preprocess(
        files_list,
        PATH_TRAIN_FORGERIES,
        final_res,
        padding)

    # There should be a total of 362 (train) + 1287 (test questioned)
    # + 646 (test reference) signatures (2295)
    message = ('Was expecting to pre-process a total of 2295 images but got {} '
               'instead'.format(n_sig))
    assert n_sig == 2295, message
