# -*- coding: utf-8 -*-
from keras.models import Model, Sequential

from keras.layers import Input, concatenate, add
from keras.layers import Dense, Activation
from keras.layers import LSTM, GRU
from keras.layers import BatchNormalization, Dropout
from keras.layers import Flatten, Reshape

from keras.layers import Conv1D, Conv2D
from keras.layers import AveragePooling1D, MaxPooling1D
from keras.layers import AveragePooling2D, MaxPooling2D
from keras.layers import GlobalAveragePooling1D, GlobalMaxPooling1D

from mas_tools.layers import Attention, AttentionWithContext, AttentionWeightedAverage

from keras.activations import relu


def cnn_model_2in(shape_a, shape_b, nb_output, activation='softmax'):
    """CNN for exchange bot.
    
    Arguments
        shape_a (): shape = (limit(timeseries or depth), features)
        shape_b (): shape = (limit(timeseries or depth), features)
        nb_output (int): Number of output classes.
        activation (string): activation function for model output.
        
    Returns
        model (keras.Model): Model of neural network."""

    assert shape_a[0] == shape_b[0]
    
    conv_nb = (16, )

    # Input A
    input_a = Input(shape=(1, shape_a[0], shape_a[1]),
                    name='input_a')
    a = BatchNormalization()(input_a)
    a = Conv2D(filters=conv_nb[0],
            kernel_size=(3, 1),
            padding='same',  # 'same' or 'causal'
            activation='relu',
            kernel_initializer='glorot_uniform',
            data_format='channels_first',
            )(a)
    a = Reshape((conv_nb[0], shape_a[0]*shape_a[1]))(a)
    a = LSTM(64,
            activation='relu',
            kernel_initializer='glorot_uniform',
            return_sequences=True
            )(a)

    # Input B
    input_b = Input(shape=(1, shape_b[0], shape_b[1]),
                    name='input_b')
    b = BatchNormalization()(input_b)
    b = Conv2D(filters=conv_nb[0],
            kernel_size=(3, 1),
            padding='same',  # 'same' or 'causal'
            activation='relu',
            kernel_initializer='glorot_uniform',
            data_format='channels_first',
            )(b)
    b = Reshape((conv_nb[0], shape_b[0]*shape_b[1]))(b)
    b = LSTM(64,
            activation='relu',
            kernel_initializer='glorot_uniform',
            return_sequences=True
            )(b)

    # Concat A and B
    x = concatenate([a, b])

    x = LSTM(96,
            activation='relu',
            kernel_initializer='glorot_uniform',
            return_sequences=True
            )(x)
    x = LSTM(32,
            activation='relu',
            kernel_initializer='glorot_uniform'
            )(x)
    output = Dense(nb_output, activation=activation)(x)

    model = Model(inputs=[input_a, input_b], outputs=output)

    return model


def cnn_model_2in_with_feedback(shape_a, shape_b, shape_fb, nb_output, activation='softmax'):
    """CNN for exchange bot.
    
    Arguments
        shape_a (tuple of int): shape = (limit(timeseries or depth), features)
        shape_b (tuple of int): shape = (limit(timeseries or depth), features)
        shape_fb (tuple of int or int): Shape of feedback data.
        nb_output (int): Number of output classes.
        activation (string): activation function for model output.
        
    Returns
        model (keras.Model): Model of neural network."""

    assert shape_a[0] == shape_b[0]
    
    conv_nb = (16, 32, 64)
    dp = 0.2

    # Input A
    input_a = Input(shape=(1, shape_a[0], shape_a[1]),
                    name='input_a')
    a = BatchNormalization()(input_a)
    a = Conv2D(filters=conv_nb[0],
            kernel_size=(5, 1),
            padding='same',  # 'same' or 'causal'
            activation='relu',
            kernel_initializer='glorot_uniform',
            data_format='channels_first',
            )(a)
    a = Conv2D(filters=conv_nb[1],
            kernel_size=(3, 1),
            padding='same',  # 'same' or 'causal'
            activation='relu',
            kernel_initializer='glorot_uniform',
            data_format='channels_first',
            )(a)
    a = MaxPooling2D(pool_size=(2,1),
            data_format='channels_first',
            )(a)
    a = Conv2D(filters=conv_nb[2],
            kernel_size=(3, 1),
            padding='same',
            activation='relu',
            kernel_initializer='glorot_uniform',
            data_format='channels_first',
            )(a)
    a = MaxPooling2D(pool_size=(2,1),
            data_format='channels_first',
            )(a)
    a = Reshape((conv_nb[2], int(shape_a[0]/4)*shape_a[1]))(a)
    a = Dense(64,
            activation='relu',
            kernel_initializer='glorot_uniform',
            # return_sequences=True
            )(a)
    a = Dropout(dp)(a)

    # Input B
    input_b = Input(shape=(1, shape_b[0], shape_b[1]),
                    name='input_b')
    b = BatchNormalization()(input_b)
    b = Reshape((1, shape_b[0] * shape_b[1]))(b)
    b = LSTM(64,
            activation='relu',
            kernel_initializer='glorot_uniform',
            return_sequences=True
            )(b)
    b = Dense(64,
            activation='relu',
            kernel_initializer='glorot_uniform',
            )(b)
    b = Dropout(dp)(b)

    # Concat A and B
    x = concatenate([a, b], axis=1)

    x = LSTM(96,
            activation='relu',
            kernel_initializer='glorot_uniform',
            return_sequences=True
            )(x)
    x = LSTM(32,
            activation='relu',
            kernel_initializer='glorot_uniform'
            )(x)
    # x = Dense(32, activation='relu')(x)
    x = Dropout(dp)(x)

    # Input Feedback
    input_fb = Input(shape=(1, shape_fb), name='input_feedback')
    fb = BatchNormalization()(input_fb)
    # fb = Flatten()(fb)
    fb = LSTM(32,
            activation='relu',
            kernel_initializer='glorot_uniform',
            )(fb)
    fb = Dropout(dp)(fb)

    # Concat X and Feedback
    x = concatenate([x, fb])

    x = Dense(10)(x)
    output = Dense(nb_output, activation=activation)(x)

    model = Model(inputs=[input_a, input_b, input_fb], outputs=output)

    return model


if __name__ == "__main__":
    path = 'E:/Projects/market-analysis-system/'

    model = cnn_model_2in((50, 9), (50, 4), 3)
    save_model_arch(model, path+'cnn2in')
    model.summary()

    model = cnn_model_2in_with_feedback((50, 9), (50, 4), 8, 3)
    save_model_arch(model, path+'cnn2in_feedback')
    model.summary()
    