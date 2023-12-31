import json
import string
import random
from flask import Flask, request, jsonify
from flask_cors import CORS
# from werkzeug.middleware.proxy_fix import ProxyFix

import nltk
import numpy as np
from nltk.stem import WordNetLemmatizer
import tensorflow as tf

nltk.download("punkt")
nltk.download("wordnet")
nltk.download('omw-1.4')

from tensorflow.keras import Sequential
from tensorflow.keras.layers import Dense, Dropout


data_file = open('intents.json').read()
data = json.loads(data_file)


words = []
classes = []
data_X = []
data_y = []

for intent in data["intents"]:
  for pattern in intent["patterns"]:
    tokens = nltk.word_tokenize(pattern)
    words.extend(tokens)
    data_X.append(pattern)
    data_y.append(intent["tag"]),
  if intent["tag"] not in classes:
    classes.append(intent["tag"])

lemmatizer = WordNetLemmatizer()

words = [lemmatizer.lemmatize(word.lower()) for word in words if word not in string.punctuation]
words = sorted(set(words))
classes = sorted(set(classes))

training = []
out_empty = [0]*len(classes)
for idx, doc in enumerate(data_X):
  bow = []
  text = lemmatizer.lemmatize(doc.lower())
  for word in words:
    bow.append(1) if word in text else bow.append(0)
  output_row = list(out_empty)
  output_row[classes.index(data_y[idx])] = 1
  training.append([bow, output_row])
random.shuffle(training)
training = np.array(training, dtype=object)
train_X = np.array(list(training[:,0]))
train_Y = np.array(list(training[:,1]))

model = Sequential()
model.add(Dense(128, input_shape = (len(train_X[0]),), activation = "relu"))
model.add(Dropout(0.5))
model.add(Dense(64, activation = "relu"))
model.add(Dropout(0.5))
model.add(Dense(len(train_Y[0]), activation = "softmax"))
adam = tf.keras.optimizers.legacy.Adam(learning_rate = 0.01, decay = 1e-6)
model.compile(loss = "categorical_crossentropy",
              optimizer = adam,
              metrics = ["accuracy"]
              )
print(model.summary())
model.fit(x=train_X, y=train_Y, epochs = 150, verbose = 1)

def clean_text(text):
  tokens = nltk.word_tokenize(text)
  tokens = [lemmatizer.lemmatize(word) for word in tokens]
  return tokens

def bag_of_words(text, vocab):
  tokens = clean_text(text)
  bow = [0]*len(vocab)
  for w in tokens:
    for idx, word in enumerate(vocab):
      if word == w:
        bow[idx] = 1
  return np.array(bow)

def pred_class(text, vocab, labels):
  bow = bag_of_words(text, vocab)
  result = model.predict(np.array([bow]))[0]
  thresh = 0.5
  y_pred = [[indx, res] for indx, res in enumerate(result) if res > thresh]
  y_pred.sort(key=lambda x: x[1], reverse = True)
  return_list = []
  for r in y_pred:
    return_list.append(labels[r[0]])
    return return_list
  
def get_response(intents_list, intents_json):
  if not isinstance(intents_list, list):
    intents_list = []

  if len(intents_list) == 0:
    result = "Sorry! I don't understand."
  else:
    result = intents_list[0]
  return result


app = Flask(__name__)
CORS(app)

@app.route('/search', methods=['GET'])
def search():
  print(request.args.get('keyword'))
  intents = pred_class(request.args.get('keyword'), words, classes)
  result = get_response(intents, data)
  response = jsonify({'response': result})
  response.headers.add('Access-Control-Allow-Origin', '*')
  return response

if __name__ == '__main__':
  app.run(debug=TRUE)
