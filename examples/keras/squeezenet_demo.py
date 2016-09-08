"""
Usage: python squeezenet_demo.py -p "/home/db/www/database/tests/train" -v -p "/home/db/www/database/tests/validation"
"""
import time
import argparse
from simdat.core import dp_tools
from simdat.core import keras_models as km
from simdat.core import tools
from keras.optimizers import SGD

dp = dp_tools.DP()
tl = tools.TOOLS()


def main():
    parser = argparse.ArgumentParser(
        description="SqueezeNet example."
        )
    parser.add_argument(
        "--epochs", type=int, default=20,
        help="Number of epochs, default 20."
        )
    parser.add_argument(
        "--lr", type=float, default=0.001,
        help="Learning rate of SGD, default 0.001."
        )
    parser.add_argument(
        "-p", "--path", type=str, default='.', required=True,
        help="Path where the images are. Default: $PWD."
        )
    parser.add_argument(
        "-v", "--val-path", type=str, default='.', required=True,
        dest='valpath', help="Path where the val images are. Default: $PWD."
        )
    parser.add_argument(
        "--img-width", type=int, default=224, dest='width',
        help="Rows of the images, default: 224."
        )
    parser.add_argument(
        "--img-height", type=int, default=224, dest='height',
        help="Columns of the images, default: 224."
        )
    parser.add_argument(
        "--channels", type=int, default=3,
        help="Channels of the images, default: 3."
        )

    args = parser.parse_args()

    train_generator = dp.train_data_generator(
        args.path, args.width, args.height)
    validation_generator = dp.val_data_generator(
        args.valpath, args.width, args.height)

    nb_train_samples = train_generator.nb_sample
    nb_val_samples = validation_generator.nb_sample
    print("[squeezenet] Number of training samples: %i " % nb_train_samples)
    print("[squeezenet] Number of training samples: %i " % nb_val_samples)
    nb_class = train_generator.nb_class
    print('[squeezenet] Total classes are %i' % nb_class)

    t0 = time.time()
    print "[squeezenet] Building the model..."
    model = km.SqueezeNet(
        nb_class, inputs=(args.channels, args.height, args.width))
    dp.visualize_model(model)

    sgd = SGD(lr=args.lr, decay=0.0002, momentum=0.9, nesterov=True)
    model.compile(
        optimizer=sgd, loss='categorical_crossentropy', metrics=['accuracy'])
    print "[squeezenet] Model built."

    print "[squeezenet] Start training..."
    model.fit_generator(
        train_generator,
        samples_per_epoch=nb_train_samples,
        nb_epoch=args.epochs,
        validation_data=validation_generator,
        nb_val_samples=nb_val_samples)

    print "[squeezenet] Model trained."

    t0 = tl.print_time(t0, 'score squeezenet')
    model.save_weights('squeeze_net.h5', overwrite=True)

if __name__ == '__main__':
    main()
