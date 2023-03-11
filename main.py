# -*- coding: utf-8 -*-
"""AlexNet CaisaV2.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1kiebkY-ok5gGtuwNL-xayWdnVmPHoJbM
"""

import os
import cv2
import numpy
from keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Lambda, Concatenate, BatchNormalization
import numpy as np
from numpy.ma import indices
from sklearn.model_selection import KFold
import keras
# from keras.models import Sequential, Input, Model
from keras.layers import Dense, Dropout, Flatten
# from keras.layers.advanced_activations import LeakyReLU
import tensorflow as tf
from tensorflow import keras
import keras.layers as layers
import tensorflow_addons as tfa
from sklearn.metrics import confusion_matrix, precision_score, recall_score, f1_score, matthews_corrcoef



DATADIR = "E:\Fourth Year\Graduation Project\pythonProject1\CoMoFoD_small_v2"

CATEGORIES = ["Au", "Sp"]

dataSet = []


def createDataSet():
    for category in CATEGORIES:
        path = os.path.join(DATADIR, category)
        class_num = CATEGORIES.index(category)
        for img in os.listdir(path):
            try:
                img_array = cv2.imread(os.path.join(path, img))
                img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                IMG_SIZE = 227
                new_array = cv2.resize(img_array, (IMG_SIZE, IMG_SIZE))
                dataSet.append([new_array, class_num])

            except Exception as e:
                print(str(e))


createDataSet()


class F1Score(tf.keras.metrics.Metric):
    def __init__(self, name='f1_score', **kwargs):
        super(F1Score, self).__init__(name=name, **kwargs)
        self.precision = tf.keras.metrics.Precision()
        self.recall = tf.keras.metrics.Recall()

    def update_state(self, y_true, y_pred, sample_weight=None):
        self.precision.update_state(y_true, y_pred, sample_weight)
        self.recall.update_state(y_true, y_pred, sample_weight)

    def result(self):
        # Compute F1 score from precision and recall
        precision = self.precision.result()
        recall = self.recall.result()
        f1_score = 2 * precision * recall / (precision + recall + tf.keras.backend.epsilon())
        return f1_score

    def reset_states(self):
        # Reset the accumulated precision and recall
        self.precision.reset_states()
        self.recall.reset_states()


model = keras.Sequential(name='alexnet_maxout_bn')


def alexnet():
    # C1
    model.add(layers.Conv2D(filters=96, kernel_size=(11, 11),
                            strides=(4, 4), padding='valid',
                            input_shape=(227, 227, 3)))
    model.add(layers.BatchNormalization())
    model.add(Lambda(lambda x: keras.backend.maximum(x[:, :, :, 0:48], x[:, :, :, 48:96])))
    model.add(layers.MaxPool2D(pool_size=(3, 3), strides=(2, 2),
                               padding='valid'))

    # C2
    model.add(layers.Conv2D(filters=256, kernel_size=(5, 5),
                            strides=(1, 1),
                            padding='same'))
    model.add(layers.BatchNormalization())
    model.add(Lambda(lambda x: keras.backend.maximum(x[:, :, :, 0:128], x[:, :, :, 128:256])))
    model.add(layers.MaxPool2D(pool_size=(3, 3), strides=(2, 2),
                               padding='valid',
                               ))

    # C3
    model.add(layers.Conv2D(filters=384, kernel_size=(3, 3),
                            strides=(1, 1),
                            padding="same"))
    model.add(layers.BatchNormalization())
    model.add(Lambda(lambda x: keras.backend.maximum(x[:, :, :, 0:192], x[:, :, :, 192:384])))

    # C4
    model.add(layers.Conv2D(filters=384, kernel_size=(3, 3),
                            strides=(1, 1),
                            padding="same"))
    model.add(layers.BatchNormalization())
    model.add(Lambda(lambda x: keras.backend.maximum(x[:, :, :, 0:192], x[:, :, :, 192:384])))

    # C5
    model.add(layers.Conv2D(filters=256, kernel_size=(3, 3),
                            strides=(1, 1),
                            padding="same"))
    model.add(layers.BatchNormalization())
    model.add(Lambda(lambda x: keras.backend.maximum(x[:, :, :, 0:128], x[:, :, :, 128:256])))
    model.add(layers.MaxPool2D(pool_size=(3, 3), padding='valid',
                               strides=(2, 2)))

    model.add(layers.Flatten())

    # FC6
    model.add(layers.Dense(4096))
    model.add(layers.BatchNormalization())
    model.add(Lambda(lambda x: keras.backend.maximum(x[:, :4096 // 2], x[:, 4096 // 2:])))
    model.add(layers.Dropout(0.5))

    # FC7
    model.add(layers.Dense(4096))
    model.add(layers.BatchNormalization())
    model.add(Lambda(lambda x: keras.backend.maximum(x[:, :4096 // 2], x[:, 4096 // 2:])))
    model.add(layers.Dropout(0.5))

    # FC8
    model.add(layers.Dense(1, activation="sigmoid"))

    # model.summary()
    model.compile(loss=keras.losses.binary_crossentropy, optimizer="sgd",
                  metrics=['accuracy', tf.keras.metrics.Precision(),
                           tf.keras.metrics.Recall(thresholds=None, top_k=None,
                                                   class_id=None, name=None, dtype=None),
                           F1Score(),
                           ])


alexnet()

import math

kf = KFold(n_splits=10, shuffle=True, random_state=0)

accuracies = []
f1Scores = []
precisions = []
MCCs = []
recalls = []

# Loop over th\e k-fold splits

for train_index, test_index in kf.split(dataSet):
    X_train = []
    y_train = []
    X_test = []
    y_test = []
    # Get the training and testing data
    for i in train_index:
        X_train.append(dataSet[i][0])
        y_train.append(dataSet[i][1])
    for j in test_index:
        X_test.append(dataSet[j][0])
        y_test.append(dataSet[j][1])

    # imgplot = plt.imshow()
    # plt.show()

    # Fit the model on the training data
    history = model.fit(np.array(X_train), np.array(y_train))

    y_pred_con = model.predict(np.array(X_test))

    floor_fn = np.vectorize(np.floor)

    y_pred = floor_fn(y_pred_con)

avg_accuracy = np.mean(history.history['accuracy'])
avg_precision = np.mean(history.history['precision'])
avg_recall = np.mean(history.history['recall'])
avg_f1_score = np.mean(history.history['f1_score'])

print("Average Accuracy:", avg_accuracy)
print("Average Precision:", avg_precision)
print("Average Recall:", avg_recall)
print("Average F1 Score:", avg_f1_score)