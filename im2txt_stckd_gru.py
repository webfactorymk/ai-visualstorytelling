from keras.models import Model
from keras.layers import Input, LSTM, Dense, Embedding, Masking, GRU, TimeDistributed
from keras.optimizers import *
from keras.callbacks import ModelCheckpoint, CSVLogger
import numpy as np
import h5py
import json
import time
import datetime
from model_data_generator import ModelDataGenerator
from seq2seqbuilder import  Seq2SeqBuilder


vocab_json = json.load(open('./dataset/vist2017_vocabulary.json'))
train_dataset = h5py.File('./dataset/image_embeddings_to_sentence/stories_to_index_train.hdf5', 'r')
valid_dataset = h5py.File('./dataset/image_embeddings_to_sentence/stories_to_index_valid.hdf5','r')
train_generator = ModelDataGenerator(train_dataset, vocab_json, 64)
valid_generator = ModelDataGenerator(valid_dataset, vocab_json, 64)
words_to_idx = vocab_json['words_to_idx']

batch_size = 13
epochs = 100 # Number of epochs to train for.
latent_dim = 1024  # Latent dimensionality of the encoding space.
word_embedding_size = 300 # Size of the word embedding space.
num_of_stacked_rnn = 2 # Number of Stacked RNN layers

learning_rate = 0.0001
gradient_clip_value = 5.0

num_samples = train_generator.num_samples
num_decoder_tokens = train_generator.number_of_tokens
valid_steps = valid_generator.num_samples / batch_size

ts = time.time()
start_time = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d_%H:%M:%S')

builder = Seq2SeqBuilder()
model = builder.build_encoder_decoder_model(latent_dim,words_to_idx, word_embedding_size, num_decoder_tokens, num_of_stacked_rnn, (None, 4096), (22,), cell_type=GRU)

#optimizer = RMSprop(lr=learning_rate, rho=0.9, epsilon=1e-08, decay=0.0, clipvalue = gradient_clip_value)
optimizer = Adam(lr=learning_rate)
model.compile(optimizer = optimizer, loss='categorical_crossentropy')
checkpoint_name=start_time+"checkpoit.hdf5"
checkpointer = ModelCheckpoint(filepath='./checkpoints/'+checkpoint_name, verbose=1, save_best_only=True)
csv_logger = CSVLogger("./loss_logs/"+start_time+".csv", separator=',', append=False)
#tensorboard = TensorBoard(log_dir='./logs', histogram_freq=0, batch_size=batch_size, write_graph=True, write_grads=True, write_images=True, embeddings_freq=0, embeddings_layer_names="embedding_layer", embeddings_metadata=None)

model.fit_generator(train_generator.multiple_samples_per_story_generator(), steps_per_epoch = num_samples / batch_size, epochs = epochs,
                    validation_data=valid_generator.multiple_samples_per_story_generator(), validation_steps=valid_steps, callbacks=[checkpointer, csv_logger])
ts = time.time()

end_time = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d_%H:%M:%S')

model.save('./trained_models/' + str(start_time)+"-"+ str(end_time)+':image_to_text_gru.h5')

