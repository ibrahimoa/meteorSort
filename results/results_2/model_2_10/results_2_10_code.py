import tensorflow as tf
from tensorflow.keras.layers import Dense,  Conv2D, MaxPooling2D, Dropout, Flatten
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.callbacks import Callback
from os.path import join
from os import listdir
import multiprocessing
from performanceMeasure import getPerformanceMeasures, plotAccuracyAndLoss, getProblematicMeteors

def trainCNN( ):

    tf.keras.backend.clear_session()

    modelNumber = 'model_2_10'
    base_dir = 'C:\work_dir\meteorData\extraData_filtered_30_split_70_30'
    results_dir = join('G:\GIEyA\TFG\meteor_classification\\results_2', modelNumber)
    results_dir_weights = join(results_dir, 'weights')

    train_dir = join(base_dir, 'train')
    validation_dir = join(base_dir, 'validation')

    ImageResolution: tuple = (432, 432)
    ImageResolutionGrayScale: tuple = (432, 432, 1)
    DROPOUT: float = 0.30
    EPOCHS: int = 50
    LEARNING_RATE: float = 5e-4

    # Training -> 62483 (3905x16)
    # Validation -> 26780 (1673x16)

    training_images = len(listdir(join(train_dir, 'meteors'))) + len(listdir(join(train_dir, 'non_meteors')))
    validation_images = len(listdir(join(validation_dir, 'meteors'))) + len(listdir(join(validation_dir, 'non_meteors')))
    batch_size: int = 24
    steps_per_epoch: int = int(training_images / batch_size)
    validation_steps: int = int(validation_images / batch_size)

    #Rescale all images by 1./255

    train_datagen = ImageDataGenerator(rescale=1.0/255)

    validation_datagen = ImageDataGenerator(rescale=1.0/255.)

    train_generator = train_datagen.flow_from_directory(train_dir,
                                                        batch_size=batch_size,
                                                        class_mode='binary',
                                                        color_mode='grayscale',
                                                        target_size=ImageResolution)

    validation_generator = validation_datagen.flow_from_directory(validation_dir,
                                                                  batch_size=batch_size,
                                                                  class_mode='binary',
                                                                  color_mode='grayscale',
                                                                  target_size=ImageResolution)

    # elu activation vs relu activation -> model_2_02 and model_2_03
    # dropout evaluation: model_2_02 (.3) vs model_2_06 (no dropout) vs model_2_07 (.4) vs model_2_08 (.5):
    # model 2.9 -> Simple CNN (5 conv layers + 2 fully-connected) -> Only 123,209 parameters. Training time: 550 s/epoch
    # model 2.10 -> 2.9 with filtered data
    # model 2.11 -> Very complex CNN (???) -> ??? parameters. Training time: ???

    model = tf.keras.models.Sequential([
        Conv2D(32, (7, 7), activation='elu', input_shape=ImageResolutionGrayScale, strides=1),
        MaxPooling2D(pool_size=(3, 3)),
        Dropout(DROPOUT),

        Conv2D(32, (5, 5), activation='elu', kernel_initializer='he_uniform'),
        MaxPooling2D(pool_size=(2, 2)),
        Dropout(DROPOUT),


        Conv2D(16, (3, 3), activation='elu', kernel_initializer='he_uniform'),
        MaxPooling2D(pool_size=(2, 2)),
        Dropout(DROPOUT),

        Conv2D(16, (3, 3), activation='elu', kernel_initializer='he_uniform'),
        MaxPooling2D(pool_size=(2, 2)),
        Dropout(DROPOUT),

        Conv2D(8, (3, 3), activation='elu', kernel_initializer='he_uniform'),
        MaxPooling2D(pool_size=(2, 2)),
        Dropout(DROPOUT),

        Flatten(),
        Dense(288, activation='elu', kernel_initializer='he_uniform'),
        Dropout(DROPOUT),
        Dense(16, activation='elu', kernel_initializer='he_uniform'),
        Dropout(DROPOUT - 0.10),
        Dense(1, activation='sigmoid', kernel_initializer='he_uniform')
    ])

    print(model.summary())
    optimizer = Adam(learning_rate=LEARNING_RATE)
    model.compile(optimizer=optimizer,
                  loss='binary_crossentropy',
                  metrics=['accuracy'])

    class SaveModelCallback(Callback):
        def __init__(self, thresholdTrain, thresholdValid):
            super(SaveModelCallback, self).__init__()
            self.thresholdTrain = thresholdTrain
            self.thresholdValid = thresholdValid

        def on_epoch_end(self, epoch, logs=None):
            if((logs.get('accuracy') >= self.thresholdTrain) and (logs.get('val_accuracy') >= self.thresholdValid)):
                model.save_weights(join(results_dir_weights, modelNumber + '_acc_' +  str(logs.get('accuracy'))[0:5]
                                        + '_val_acc_' + str(logs.get('val_accuracy'))[0:5] + '.h5'), save_format='h5')

    callback_88_88 = SaveModelCallback(0.880, 0.880)

    history = model.fit(train_generator,
                        validation_data=validation_generator,
                        steps_per_epoch=steps_per_epoch,
                        epochs=EPOCHS, #Later train with more epochs if neccessary
                        validation_steps=validation_steps,
                        shuffle=True,
                        verbose=1,
                        callbacks=[callback_88_88])

    #     model.load_weights(join(results_dir_weights, 'model_2_09_acc_0.917_val_acc_0.882.h5'))
    #     dataDir = 'C:\work_dir\meteorData\extra_data'
    #     problematicFile = join('G:\GIEyA\TFG\meteor_classification\\results_2', 'problematicData_48.txt')
    #     getProblematicMeteors(model, dataDir, ImageResolution, problematicFile, margin=0.48)

    ################################# PRINT MODEL PERFORMANCE AND GET PERFORMANCE MEASURES  #################################

    # Get performance measures:
    getPerformanceMeasures(model, validation_dir, ImageResolution, join(results_dir, 'performance_' + modelNumber + '.txt'), threshold=0.50)

    # Plot Accuracy and Loss in both train and validation sets
    plotAccuracyAndLoss(history)

    #########################################################################################################################

if __name__ == '__main__':
    p = multiprocessing.Process(target=trainCNN)
    p.start()
    p.join()
