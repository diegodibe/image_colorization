# -*- coding: utf-8 -*-
"""colorization_CAE.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1ZlzzNE00UhYpiXNr75p6HMxlYGaPepYR
"""

# Commented out IPython magic to ensure Python compatibility.
import tensorflow as tf
import numpy as np
from PIL import Image
from matplotlib import pyplot as plt
from tensorflow.keras.models import Sequential
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.layers import Conv2D, MaxPooling2D, UpSampling2D, BatchNormalization, Activation

# %matplotlib inline
(x_train, y_train), (x_test, y_test) = tf.keras.datasets.cifar10.load_data()
x_complete = np.concatenate([x_train, x_test])

np.random.shuffle(x_complete)
rgb_img = []
print(x_complete.shape)

#rgb to YCbCr
x_complete_img = ([Image.fromarray(np.uint8(i), 'RGB') for i in x_complete])
ycbcr_img = ([i.convert('YCbCr') for i in x_complete_img])


#split in channels
y_img = []
cb_img = []
cr_img = []
for i in range(len(ycbcr_img)):
  y, cb, cr = (Image.Image.split(ycbcr_img[i]))
  y_img.append(y)
  cb_img.append(cb)
  cr_img.append(cr)

y_channel_norm = np.asarray([np.asarray(i) / 255.0 for i in y_img])
cb_channel_norm = np.asarray([np.asarray(i) / 255.0 for i in cb_img])
cr_channel_norm = np.asarray([(np.asarray(i)) / 255.0  for i in cr_img]) # 3 min value in dataset

cbcr_channel_norm = np.stack((cb_channel_norm, cr_channel_norm), axis=3)

# adapted from: https://stackoverflow.com/questions/41908379/keras-plot-training-validation-and-test-set-accuracy
def plot_error(history, learning_rate, batch_size, description):
    plt.plot(history.history['loss'])
    plt.plot(history.history['val_loss'])
    plt.title(f'model loss with learning rate {learning_rate} and batch size {batch_size}')
    plt.ylabel('loss')
    plt.xlabel('epoch')
    plt.legend(['train', 'validation'], loc='upper right')
    plt.savefig(f'{description}.png')

train_size = int(0.8 * len(x_complete))
val_size = int(0.1 * len(x_complete))

y_channel_norm = y_channel_norm[:, :, :, None]

x_train = y_channel_norm[:train_size]
x_val = y_channel_norm[train_size:train_size+val_size]
x_test = y_channel_norm[train_size+val_size:]

y_train = cbcr_channel_norm[:train_size]
y_val = cbcr_channel_norm[train_size:train_size+val_size]
y_test = cbcr_channel_norm[train_size+val_size:]

y_train_org = x_complete[:train_size] / 255.0
y_val_org = x_complete[train_size+val_size:] / 255.0
y_test_org = x_complete[train_size+val_size:] / 255.0

print(x_train.shape, x_val.shape,  x_test.shape)
print(y_train.shape, y_val.shape,  y_test.shape)

model = Sequential([
            Conv2D(filters=8, kernel_size=(3, 3), strides=(1, 1), input_shape=(32, 32, 1), padding='same'),
            Activation("relu"),
            Conv2D(filters=16, kernel_size=(3, 3), strides=(1, 1), padding='same'),
            Activation("relu"),
            Conv2D(filters=32, kernel_size=(3, 3), strides=(2, 2), padding='same'),
            Activation("relu"),
            Conv2D(filters=64, kernel_size=(3, 3), strides=(2, 2), padding='same'),
            Activation("relu"),
            Conv2D(filters=64, kernel_size=(3, 3), strides=(1, 1), padding='same'),
            Activation("relu"),
            UpSampling2D(size=(2, 2)),
            Conv2D(filters=64, kernel_size=(2, 2), strides=(1, 1), padding='same'),
            Activation("relu"),
            UpSampling2D(size=(2, 2)),
            Conv2D(filters=32, kernel_size=(2, 2), strides=(1, 1), padding='same'),
            Activation("relu"),
            Conv2D(filters=16, kernel_size=(2, 2), strides=(1, 1), padding='same'),
            Activation("relu"),
            Conv2D(filters=2, kernel_size=(2, 2), strides=(1, 1), activation='sigmoid',
                   padding='same'),
        ])
model.save_weights('model.h5')
print(model.summary())

no_epochs = 10
train = True

# learning_rate = [0.1, 0.01, 0.001, 0.0001]
# batch_sizes = [32, 128, 512, 1000]
learning_rate = [0.001]
batch_sizes = [128]
description = "test"

if train:
    for l, b in [(l, b) for l in learning_rate for b in batch_sizes]:
      model.load_weights('model.h5')
      opt = tf.keras.optimizers.Adam()
      model.compile(optimizer=opt, loss='mse', metrics=['mse'])

      tf.keras.utils.plot_model(model, to_file=f'model_plot_{description}.png', show_shapes=True, show_layer_names=False)

      history = model.fit(x_train, y_train, batch_size=b,
                            validation_data=(x_val, y_val), epochs=no_epochs, verbose=1)

      plot_error(history, l, b, description)
      plt.show()
      model.save("my_model2")
else:
    model = tf.keras.models.load_model("my_model2")

print('\n# Evaluate on test data')
results = model.evaluate(x_test, y_test, verbose=1)

print('\n# Predict on test data')
predictions = model.predict(x_test, steps=1, verbose=1)

print(x_test.shape)
print(y_test.shape)
ycbcr_pred_channel = np.concatenate((x_test, predictions), axis=3)
ycbcr_pred_channel = np.uint8(ycbcr_pred_channel * 255.0)
ycbcr_pred_img = ([Image.fromarray(i, mode="YCbCr") for i in ycbcr_pred_channel])

rgb_pred_img = ([i.convert("RGB") for i in ycbcr_pred_img])

# rgb_pred_img = predictions

plt.figure()

rows = 5
cols = 3
c_plot = 1
c_img = 0

for i in range(rows):
  for j in range(cols):
    plt.subplot(rows, cols * 3, c_plot); plt.imshow(y_test_org[c_img]); plt.axis('off')
    c_plot += 1
    plt.subplot(rows, cols * 3, c_plot); plt.imshow(x_test[c_img,:,:,-1], cmap="gray"); plt.axis('off')
    c_plot += 1
    plt.subplot(rows, cols * 3, c_plot); plt.imshow(rgb_pred_img[c_img]); plt.axis('off')
    c_plot += 1
    c_img += 1
plt.tight_layout()

plt.show()