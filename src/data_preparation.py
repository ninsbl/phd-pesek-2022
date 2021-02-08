#!/usr/bin/python3

import os
import rasterio

import numpy as np
import tensorflow as tf


def convert_to_tensor(fname, tensor_shape=(256, 256), normalize_data=False):
    """Convert an ndarray to a tensor while resizing and normalizing it.

    :param fname: ndarray with an image
    :param tensor_shape: shape of the first two dimensions of output tensors
    :param normalize_data: boolean saying whether or not should the data be
        normalized to range (-1, 1)
    :return: a processed tensor
    """
    # TODO: experiment with the followings
    #img_strings = tf.io.read_file(fname)
    # imgs_decoded = tf.image.decode_jpeg(img_strings)
    # imgs_decoded = tfio.experimental.image.decode_tiff(img_strings)
    # a = rasterio.open(img_strings)
    # imgs_decoded = a.read()

    # Resize the image
    output = tf.image.resize(fname, tensor_shape)

    # TODO: experiment with normalization
    # TODO: does it really normalize to range (-1, 1)?
    # TODO: should not be a hard-coded value
    # Normalize if required
    if normalize_data:
        output = (output - 128) / 128

    return output


# TODO: get rid of the rasterio dependency
def read_images(data_dir, tensor_shape=(256, 256), verbose=1):
    """Read images and return them as tensors and lists of filenames.

    :param data_dir: path to the directory containing images
    :param tensor_shape: shape of the first two dimensions of input tensors
    :param verbose: verbosity (0=quiet, >0 verbose)
    :return: image_tensors, masks_tensors, images_filenames, masks_filenames
    """
    # Get the file names list from provided directory
    file_list = [f for f in os.listdir(data_dir) if
                 os.path.isfile(os.path.join(data_dir, f))]
    file_list = sorted(file_list)

    # when sorted, images 1 to 10 are not followed by their labels
    for i in [str(j) for j in range(1, 11)]:
        string = 'image_{}.tif'.format(i)
        string_L = 'image_{}_L.tif'.format(i)
        file_list.remove(string_L)
        file_list.insert(file_list.index(string) + 1, string_L)

    # Separate frame and mask files lists, exclude unnecessary files
    images_filenames = [file for file in file_list if
                        ('_L' not in file) and ('txt' not in file)]
    masks_filenames = [file for file in file_list if
                       ('_L' in file) and ('txt' not in file)]

    if verbose > 0:
        print('{} image files found in the provided directory.'.format(
            len(images_filenames)))
        print('{} mask files found in the provided directory.'.format(
            len(masks_filenames)))

    # Create file paths from file names
    images_paths = [os.path.join(data_dir, fname) for fname in images_filenames]
    masks_paths = [os.path.join(data_dir, fname) for fname in masks_filenames]

    # TODO: Check the possibility of moving the following to
    #       convert_to_tensor()
    # Create dataset of np arrays
    images_arrays = [rasterio.open(i, 'r').read() for i in images_paths]
    images_arrays = [np.transpose(i, (1, 2, 0)) for i in images_arrays]
    masks_arrays = [rasterio.open(i, 'r').read() for i in masks_paths]
    masks_arrays = [np.transpose(i, (1, 2, 0)) for i in masks_arrays]

    # TODO: this step could exceed the free system memory and be slow
    # create tf dataset
    images_data = tf.data.Dataset.from_tensor_slices(images_arrays)
    masks_data = tf.data.Dataset.from_tensor_slices(masks_arrays)

    image_tensors = images_data.map(
        lambda x: convert_to_tensor(x, tensor_shape))
    masks_tensors = masks_data.map(
        lambda x: convert_to_tensor(x, tensor_shape))

    # TODO: benchmark the way above with the following
    # Read images into the tensor dataset
    #frame_data = list(map(rasterio.open, images_paths))
    #frame_data = [i.read() for i in frame_data]
    #frame_tensors = tf.convert_to_tensor(frame_data)
    #mask_data = list(map(rasterio.open, masks_paths))
    #mask_data = [i.read() for i in mask_data]
    #masks_tensors = tf.convert_to_tensor(mask_data)

    if verbose > 0:
        print('Completed importing {} images from the provided '
              'directory.'.format(len(images_filenames)))
        print('Completed importing {} masks from the provided '
              'directory.'.format(len(masks_filenames)))

    return image_tensors, masks_tensors, images_filenames, masks_filenames


def parse_label_code(line):
    """Parse lines in a text file into a label code and a label name.

    :param line: line in the txt file
    :return: tuple with an integer label code, a string label name
    """
    # TODO: do not use tabulators
    a, b = line.strip().split("\t")

    # TODO: why am I returning a tuple?
    return (int(a), ), b


# TODO: get rid of the rasterio dependency
def generate_dataset_structure(data_dir, nr_bands=12, tensor_shape=(256, 256),
                               verbose=1):
    """Generate the expected dataset structure.

    Will generate directories train_images, train_masks, val_images and
    val_masks.

    :param data_dir: path to the directory containing images
    :param nr_bands: number of bands of intended input images
    :param tensor_shape: shape of the first two dimensions of input tensors
    :param verbose: verbosity (0=quiet, >0 verbose)
    """
    # Create folders to hold images and masks
    dirs = ['train_images', 'train_masks', 'val_images', 'val_masks']

    for directory in dirs:
        dir_full_path = os.path.join(data_dir, directory)
        if not os.path.isdir(dir_full_path):
            os.makedirs(dir_full_path)

    images, masks, images_filenames, masks_filenames = read_images(
        data_dir, tensor_shape)

    # TODO: would be nice to avoid tf.compat.v1 (stay v2) (what about my
    #       generator?)
    # Create iterators for images and masks
    # outside of TF Eager, we would use make_one_shot_iterator
    frame_batches = tf.compat.v1.data.make_one_shot_iterator(images)
    mask_batches = tf.compat.v1.data.make_one_shot_iterator(masks)

    # Iterate over the train images while saving the images and masks in appropriate folders
    dir_name = 'train'
    # TODO: Experiment with uint16
    # TODO: parameterize shape
    # TODO: read crs automatically
    frame_profile = {'driver': 'GTiff', 'nodata': None,
                     'height': tensor_shape[0], 'width': tensor_shape[1],
                     'count': nr_bands,
                     'crs': rasterio.crs.CRS.from_epsg(32633), 'tiled': False,
                     'interleave': 'pixel', 'dtype': 'uint8'}
    mask_profile = {'driver': 'GTiff', 'nodata': None,
                    'height': tensor_shape[0], 'width': tensor_shape[1],
                    'count': 1,
                    'crs': rasterio.crs.CRS.from_epsg(32633), 'tiled': False,
                    'interleave': 'pixel', 'dtype': 'uint8'}

    with rasterio.Env():
        # TODO: make train-val division a parameter
        for file in zip(images_filenames[:-round(0.2 * len(images_filenames))],
                        masks_filenames[:-round(0.2 * len(masks_filenames))]):
            # TODO: Experiment with uint16
            # Convert tensors to numpy arrays
            image = (frame_batches.next().numpy() / 255).astype(np.uint8)
            mask = mask_batches.next().numpy().astype(np.uint8)

            image = np.transpose(image, (2, 0, 1))
            mask = np.transpose(mask, (2, 0, 1))
            # TODO: https://stackoverflow.com/questions/53776506/how-to-save-an-array-representing-an-image-with-40-band-to-a-tif-file

            image_path = os.path.join(data_dir, '{}_images'.format(dir_name),
                                      file[0])
            mask_path = os.path.join(data_dir, '{}_masks'.format(dir_name),
                                     file[0])
            with rasterio.open(image_path, 'w', **frame_profile) as dst:
                dst.write(image)
            with rasterio.open(mask_path, 'w', **mask_profile) as dst:
                dst.write(mask)

        # TODO: Join train and val part into one chunk of code
        # Iterate over the val images while saving the images and masks in appropriate folders
        dir_name = 'val'
        # TODO: make train-val division a parameter
        for file in zip(images_filenames[-round(0.2 * len(images_filenames)):],
                        masks_filenames[-round(0.2 * len(masks_filenames)):]):
            # TODO: Experiment with uint16
            # Convert tensors to numpy arrays
            image = (frame_batches.next().numpy() / 255).astype(np.uint8)
            mask = mask_batches.next().numpy().astype(np.uint8)

            image = np.transpose(image, (2, 0, 1))
            mask = np.transpose(mask, (2, 0, 1))

            image_path = os.path.join(data_dir, '{}_images'.format(dir_name),
                                      file[0])
            mask_path = os.path.join(data_dir, '{}_masks'.format(dir_name),
                                     file[0])
            with rasterio.open(image_path, 'w', **frame_profile) as dst:
                dst.write(image)
            with rasterio.open(mask_path, 'w', **mask_profile) as dst:
                dst.write(mask)

        if verbose > 0:
            print("Saved {} images to directory {}".format(
                len(images_filenames), data_dir))
            print("Saved {} masks to directory {}".format(
                len(masks_filenames), data_dir))
