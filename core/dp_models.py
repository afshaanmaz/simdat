import sys
import h5py
import theano
import numpy as np
import scipy as sp
from collections import OrderedDict
from sklearn import cluster
from simdat.core import image
from keras.models import Sequential
from keras.layers.core import Flatten, Dense, Dropout
from keras.layers.convolutional import Convolution2D, MaxPooling2D
from keras.layers.convolutional import ZeroPadding2D
from keras.utils import np_utils


class DP:
    def __init__(self):
        pass

    def extract_hypercolumn(self, model, la_idx, instance):
        ''' Extract HyperColumn of pixels

        @param model: input DP model
        @param la_idx: indexes of the layers to be extract
        @param instamce: image instance used to extract the hypercolumns

        '''
        layers = [model.layers[li].get_output(train=False) for li in la_idx]
        get_feature = theano.function([model.layers[0].input], layers,
                                      allow_input_downcast=False)
        feature_maps = get_feature(instance)
        hypercolumns = []
        for convmap in feature_maps:
            for fmap in convmap[0]:
                upscaled = sp.misc.imresize(fmap, size=(224, 224),
                                            mode="F", interp='bilinear')
                hypercolumns.append(upscaled)
        return np.asarray(hypercolumns)

    def cluster_hc(self, hc, n_jobs=1):
        ''' Use KMeans to cluster hypercolumns'''

        ori_size = hc.shape[1]
        new_size = ori_size*ori_size
        m = hc.transpose(1, 2, 0).reshape(new_size, -1)
        kmeans = cluster.KMeans(n_clusters=2, max_iter=300, n_jobs=n_jobs,
                                precompute_distances=True)
        cluster_labels = kmeans .fit_predict(m)
        imcluster = np.zeros((ori_size, ori_size))
        imcluster = imcluster.reshape((new_size,))
        imcluster = cluster_labels
        return imcluster.reshape(ori_size, ori_size)

    def prepare_data(self, path, img_rows, img_cols):
        """ Read images as dp inputs

        @param path: path of the parent folder of images
        @param img_rows: number rows used to resize the images
        @param img_cols: number columns used to resize the images

        """

        from simdat.core import image
        from simdat.core import ml
        im = image.IMAGE()
        mlr = ml.MLRun()

        imgs = im.find_images(dir_path=path)
        X = []
        Y = []
        classes = {}
        counter = 0
        for fimg in imgs:
            if counter % 20 == 0:
                print('Reading images: %i' % counter)
            _cls_ix = mlr.get_class_from_path(fimg)
            if _cls_ix not in classes:
                classes[_cls_ix] = len(classes)
            _img_original = im.read(fimg, size=(img_rows, img_cols))
            if _img_original is None:
                continue
            _img = _img_original.transpose((2, 0, 1))
            X.append(_img)
            Y.append(classes[_cls_ix])
            counter += 1

        nb_classes = len(classes)

        X = np.array(X)
        Y = np.array(Y)

        X_train, X_test, y_train, y_test = mlr.split_samples(X, Y)
        X_train = X_train.astype('float32')
        X_test = X_test.astype('float32')
        X_train /= 255
        X_test /= 255

        # convert class vectors to binary class matrices
        Y_train = np_utils.to_categorical(y_train, nb_classes)
        Y_test = np_utils.to_categorical(y_test, nb_classes)
        print('[DP] X_train shape: (%i, %i)'
              % (X_train.shape[0], X_train.shape[1]))
        print('[DP] Y_train shape: (%i, %i)'
              % (Y_train.shape[0], Y_train.shape[1]))
        print('[DP] %i train samples' % X_train.shape[0])
        print('[DP] %i test samples' % X_test.shape[0])
        return X_train, X_test, Y_train, Y_test, classes


class DPModel(DP):
    def __init__(self):
        self.layers = None
        self.dpmodel_init()

    def dpmodel_init(self):
        """ place holder for child class """
        pass

    def VGG_19(self, weights_path=None):
        '''VGG-19 model, source from https://goo.gl/rvcNDw'''

        self.layers = OrderedDict([
            ('conv1', [
                ZeroPadding2D((1, 1), input_shape=(3, 224, 224)),
                Convolution2D(64, 3, 3, activation='relu'),
                ZeroPadding2D((1, 1)),
                Convolution2D(64, 3, 3, activation='relu'),
                MaxPooling2D((2, 2),  strides=(2, 2))
            ]),
            ('conv2', [
                ZeroPadding2D((1, 1)),
                Convolution2D(128, 3, 3, activation='relu'),
                ZeroPadding2D((1, 1)),
                Convolution2D(128, 3, 3, activation='relu'),
                MaxPooling2D((2, 2), strides=(2, 2))
            ]),
            ('conv3', [
                ZeroPadding2D((1, 1)),
                Convolution2D(256, 3, 3, activation='relu'),
                ZeroPadding2D((1, 1)),
                Convolution2D(256, 3, 3, activation='relu'),
                ZeroPadding2D((1, 1)),
                Convolution2D(256, 3, 3, activation='relu'),
                ZeroPadding2D((1, 1)),
                Convolution2D(256, 3, 3, activation='relu'),
                MaxPooling2D((2, 2), strides=(2, 2))
            ]),
            ('conv4', [
                ZeroPadding2D((1, 1)),
                Convolution2D(512, 3, 3, activation='relu'),
                ZeroPadding2D((1, 1)),
                Convolution2D(512, 3, 3, activation='relu'),
                ZeroPadding2D((1, 1)),
                Convolution2D(512, 3, 3, activation='relu'),
                ZeroPadding2D((1, 1)),
                Convolution2D(512, 3, 3, activation='relu'),
                MaxPooling2D((2, 2), strides=(2, 2))
            ]),
            ('conv5', [
                ZeroPadding2D((1, 1)),
                Convolution2D(512, 3, 3, activation='relu'),
                ZeroPadding2D((1, 1)),
                Convolution2D(512, 3, 3, activation='relu'),
                ZeroPadding2D((1, 1)),
                Convolution2D(512, 3, 3, activation='relu'),
                ZeroPadding2D((1, 1)),
                Convolution2D(512, 3, 3, activation='relu'),
                MaxPooling2D((2, 2), strides=(2, 2))
            ]),
            ('fc', [
                Flatten(),
                Dense(4096, activation='relu'),
                Dropout(0.5),
                Dense(4096, activation='relu'),
                Dropout(0.5),
            ]),
            ('classify', [
                Dense(1000, activation='softmax')
            ])
        ])
        model = Sequential()
        for stack in self.layers:
            for l in self.layers[stack]:
                model.add(l)

        if weights_path:
            model.load_weights(weights_path)

        return model

    def VGG_16(self, weights_path=None, lastFC=True):
        '''VGG-16 model, source from https://goo.gl/qqM88H'''

        self.layers = OrderedDict([
            ('conv1', [
                ZeroPadding2D((1, 1), input_shape=(3, 224, 224)),
                Convolution2D(64, 3, 3, activation='relu'),
                ZeroPadding2D((1, 1)),
                Convolution2D(64, 3, 3, activation='relu'),
                MaxPooling2D((2, 2),  strides=(2, 2))
            ]),
            ('conv2', [
                ZeroPadding2D((1, 1)),
                Convolution2D(128, 3, 3, activation='relu'),
                ZeroPadding2D((1, 1)),
                Convolution2D(128, 3, 3, activation='relu'),
                MaxPooling2D((2, 2), strides=(2, 2))
            ]),
            ('conv3', [
                ZeroPadding2D((1, 1)),
                Convolution2D(256, 3, 3, activation='relu'),
                ZeroPadding2D((1, 1)),
                Convolution2D(256, 3, 3, activation='relu'),
                ZeroPadding2D((1, 1)),
                Convolution2D(256, 3, 3, activation='relu'),
                MaxPooling2D((2, 2), strides=(2, 2))
            ]),
            ('conv4', [
                ZeroPadding2D((1, 1)),
                Convolution2D(512, 3, 3, activation='relu'),
                ZeroPadding2D((1, 1)),
                Convolution2D(512, 3, 3, activation='relu'),
                ZeroPadding2D((1, 1)),
                Convolution2D(512, 3, 3, activation='relu'),
                MaxPooling2D((2, 2), strides=(2, 2))
            ]),
            ('conv5', [
                ZeroPadding2D((1, 1)),
                Convolution2D(512, 3, 3, activation='relu'),
                ZeroPadding2D((1, 1)),
                Convolution2D(512, 3, 3, activation='relu'),
                ZeroPadding2D((1, 1)),
                Convolution2D(512, 3, 3, activation='relu'),
                MaxPooling2D((2, 2), strides=(2, 2))
            ]),
            ('fc', [
                Flatten(),
                Dense(4096, activation='relu'),
                Dropout(0.5),
                Dense(4096, activation='relu'),
                Dropout(0.5),
            ]),
            ('classify', [
                Dense(1000, activation='softmax')
            ])
        ])
        model = Sequential()
        for stack in self.layers:
            if stack == 'classify' and not lastFC:
                print('[DPModels] Skip the last FC layer')
                continue
            for l in self.layers[stack]:
                model.add(l)

        if weights_path:
            self.load_weights(model, weights_path, lastFC=lastFC)

        return model

    def load_weights(self, model, weights_path, lastFC=True):
        """ Load model weights

        @param model: the model
        @param weight_path: path of the weight file

        Arguments:

        lastFC -- True to load weights for the last FC layer (default: True)

        """
        if lastFC:
            model.load_weights(weights_path)
            return
        f = h5py.File(weights_path)
        for k in range(f.attrs['nb_layers']):
            if k >= len(model.layers):
                break
            g = f['layer_{}'.format(k)]
            weights = [g['param_{}'.format(p)] for p in range(g.attrs['nb_params'])]
            model.layers[k].set_weights(weights)
        f.close()
        return

    def Simple(self, cats, img_row=224, img_col=224, conv_size=3,
               colors=3, weights_path=None, filter_size=32):
        '''Simple conv model to the best MNIST result.
           The input shape should be (n_imgs, colors, img_row, img_col).

        @param cats: total number of final categories

        Arguments:
        img_row -- number of rows of the image
        img_col -- number of cols of the image
        conv_size -- size of the conv window
        colors  -- colors of the image (3 for RGB)
        weights_path -- used for loading the existing model
        filter_size -- number of the filters of the first conv layer

        '''
        self.layers = OrderedDict([
            ('conv1', [
                Convolution2D(filter_size, conv_size, conv_size,
                              activation='relu', border_mode='valid',
                              input_shape=(colors, img_row, img_col)),
                Convolution2D(filter_size*2, conv_size, conv_size,
                              activation='relu'),
                MaxPooling2D((2, 2),  strides=(1, 1)),
                Dropout(0.25)
            ]),
            ('fc', [
                Flatten(),
                Dense(128, activation='relu'),
                Dropout(0.5),
            ]),
            ('classify', [
                Dense(cats, activation='softmax')
            ])
        ])
        model = Sequential()
        for stack in self.layers:
            for l in self.layers[stack]:
                model.add(l)

        if weights_path:
            model.load_weights(weights_path)

        return model


class ImageNet(image.IMAGE):
    def get_labels(self, fname='synset_words.txt'):
        '''Get ImageNet labels from file'''

        if not self.check_exist(fname):
            print('ERROR: Cannot find %s.' % fname)
            sys.exit(1)
        return np.loadtxt(fname, str, delimiter='\t')

    def find_topk(self, prob, labels=None, fname='synset_words.txt', ntop=3):
        ''' Find the categories with highest probabilities

        @param prob: a list of probabilities of 1,000 categories

        Keyword arguments:
        labels -- ImageNet labels (default: re-gain from self.get_labels)
        fname  -- filename of the ImageNet labels
        ntop   -- how many top cats to be shown (default: 3)

        @retuen results = {INDEX: (probability, label, [cats])}
         example: {955: (0.00051713100401684642, 'n07754684',
                   ['jackfruit', 'jak', 'jack'])}

        '''
        if labels is None:
            labels = self.get_labels(fname)
        results = {}
        top_k = prob.flatten().argsort()[-1:-(ntop+1):-1]
        for k in top_k:
            l = labels[k].replace(',', '').split(' ')
            results[k] = (prob[k], l[0], l[1:])
        return results
