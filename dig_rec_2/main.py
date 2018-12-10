__version__ = "1.10.1"

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.graphics import Color, Ellipse, Line
from kivy.core.window import Window
from kivy.properties import NumericProperty, ReferenceListProperty, ObjectProperty, Property
from kivy.uix.label import Label

from kivy.graphics.texture import Texture
from kivy.graphics import Rectangle

from abc import ABC, abstractmethod
import numpy as np
from urllib.request import urlopen

import pickle
import os
import PIL
import time

nn = None
digit_line = []


class DigitPaint(Widget):
    def on_touch_down(self, touch):
        with self.canvas:
            Color(1, 0, 0)
            touch.ud['line'] = Line(points=(touch.x, touch.y), width=30)

    def on_touch_move(self, touch):
        touch.ud['line'].points += [touch.x, touch.y]
        digit_line.append([int(touch.x), int(touch.y)])
        self.line = touch.ud['line']


class MainWidget(Widget):
    current = NumericProperty(0)

    prob_0 = NumericProperty(0)
    prob_1 = NumericProperty(0)
    prob_2 = NumericProperty(0)
    prob_3 = NumericProperty(0)
    prob_4 = NumericProperty(0)
    prob_5 = NumericProperty(0)
    prob_6 = NumericProperty(0)
    prob_7 = NumericProperty(0)
    prob_8 = NumericProperty(0)
    prob_9 = NumericProperty(0)

    max_prob = NumericProperty(1)

    path = Property("")

    def set_pred(self, pred):
        self.current = int(pred)

    def set_path(self, path):
        self.path = str(path)

    def draw_prob_rect(self, pred_arr):
        self.prob_0 = pred_arr[0]
        self.prob_1 = pred_arr[1]
        self.prob_2 = pred_arr[2]
        self.prob_3 = pred_arr[3]
        self.prob_4 = pred_arr[4]
        self.prob_5 = pred_arr[5]
        self.prob_6 = pred_arr[6]
        self.prob_7 = pred_arr[7]
        self.prob_8 = pred_arr[8]
        self.prob_9 = pred_arr[9]

        self.max_prob = max(pred_arr)


class RecogApp(App):
    def build(self):
        self.parent = MainWidget()
        self.painter = DigitPaint()

        clearbtn = Button(text='Clear', pos=(0, 110))
        clearbtn.bind(on_release=self.clear_canvas)

        recogbtn = Button(text='Rec', pos=(0, 220))
        recogbtn.bind(on_release=self.digit_rec)

        exitbtn = Button(text='Exit', pos=(0, 0))
        exitbtn.bind(on_release=self.exit_btn)

        self.parent.add_widget(self.painter)
        self.parent.add_widget(recogbtn)
        self.parent.add_widget(clearbtn)
        self.parent.add_widget(exitbtn)

        return self.parent

    def clear_canvas(self, obj):
        global digit_line
        self.painter.canvas.clear()
        digit_line = []

    def digit_rec(self, obj):
        global digit_line

        w = self.parent.width
        h = self.parent.height

        if not nn:
            build_nn(self.user_data_dir)

        # start = time.time()
        # img = draw_from_line(w, h)
        # print('draw: ', time.time() - start)
        #
        # start = time.time()
        img_2 = draw_from_line_2(w, h)
        # print('draw_2: ', time.time() - start)
        #
        # start = time.time()
        prediction = predict(img_2)
        # print('pred: ', time.time() - start)

        prediction = prediction[0][0]

        self.parent.set_pred(np.argmax(prediction))

        int_pred = []
        for i, num in enumerate(prediction):
            int_pred.append(int(num * 100))

        self.parent.draw_prob_rect(int_pred)

    def exit_btn(self, *kwargs):
        self.stop()


def draw_from_line(w, h):
    global digit_line

    cut_h_down = 330
    cut_h_up = 30

    cut_w_left = 125
    cut_w_right = 30

    # image = PIL.Image.new(mode='1', size=(w, h))
    # draw = PIL.ImageDraw.Draw(image)
    #
    # for i in range(len(digit_line) - 1):
    #     draw.line((digit_line[i][0], digit_line[i][1], digit_line[i + 1][0], digit_line[i + 1][1]), fill=1, width=20)
    #
    # area = (130, 30, w - 30, h - 30)
    # image = image.crop(area)

    image = np.zeros((h, w))

    for point in digit_line:
        x = point[0]
        y = point[1]
        for x_it in range(x - 15, x + 15):
            if w > x_it > 0:
                for y_it in range(y - 15, y + 15):
                    if h > y_it > 0:
                        dist_vec = [x - x_it, y - y_it]
                        dist = np.linalg.norm(dist_vec)

                        if dist < 15:
                            image[y_it, x_it] = 1

    image = image[cut_h_down:(h - cut_h_up), cut_w_left:(w - cut_w_right)]
    image = image[::-1]
    image = PIL.Image.fromarray(image)
    image = image.resize((28, 28), PIL.Image.ANTIALIAS)
    image = np.asarray(image)

    return image


def draw_from_line_2(w, h):
    global digit_line
    # print(w, h)

    valid_line = []

    # decrease factor must be even
    dec_fact = 4
    line_width = 30

    cut_h_down = 330
    cut_h_up = 30

    cut_w_left = 125
    cut_w_right = 30

    # crop line on image
    for point in digit_line:
        x = point[0]
        y = point[1]

        if w - cut_w_right > x > cut_w_left:
            if h - cut_h_up > y > cut_h_down:
                n_x = x - cut_w_left
                n_y = y - cut_h_down

                valid_line.append([n_x, n_y])

    h = h - (cut_h_up + cut_h_down)
    w = w - (cut_w_left + cut_w_right)

    if h % 2 != 0:
        h += 1
    if w % 2 != 0:
        w += 1

    # decrease resolution
    h = h // dec_fact
    w = w // dec_fact
    image = np.zeros((h, w))
    line_width = line_width // dec_fact

    # fill the image with line
    for point in valid_line:
        x = point[0] // dec_fact
        y = point[1] // dec_fact
        for x_it in range(x - (line_width // 2), x + (line_width // 2)):
            if w > x_it > 0:
                for y_it in range(y - (line_width // 2), y + (line_width // 2)):
                    if h > y_it > 0:
                        dist_vec = [x - x_it, y - y_it]
                        dist = np.linalg.norm(dist_vec)

                        if dist < (line_width // 2):
                            image[y_it, x_it] = 1

    image = image[::-1]
    image = PIL.Image.fromarray(image)
    image = image.resize((28, 28), PIL.Image.ANTIALIAS)
    image = np.asarray(image)

    return image


def predict(im):
    global nn

    # import matplotlib.pyplot as plt
    # plt.subplot(2, 1, 1)
    # plt.imshow(im)
    # plt.subplot(2, 1, 2)
    # plt.imshow(im_2)
    # plt.show()

    gray_image = im.reshape(1, 1, -1)

    prediction = nn.predict(gray_image)

    return prediction


def download_file(save_dir, url):
    local_filename = url.split('/')[-1]
    local_file = os.path.join(save_dir, local_filename)

    response = urlopen(url + "?raw=true")
    CHUNK = 16 * 1024
    with open(local_file, 'wb') as f:
        while True:
            chunk = response.read(CHUNK)
            if not chunk:
                break
            f.write(chunk)

    # save_dir = self.user_data_dir
    # save_dir = "/home/biot"
    # local_filename = url.split('/')[-1]
    # local_file = os.path.join(save_dir, local_filename)
    # response = requests.get(url, stream=True)
    # with open(local_file, 'wb') as f:
    #     for chunk in response.iter_content(chunk_size=1024):
    #         if chunk:
    #             f.write(chunk)
    #             f.flush()

    return local_file


def build_nn(save_dir):
    global nn

    num_class = 10

    ip = Input(input_size=(1, 784))
    # x = Conv2d(number_of_kernel=3, kernel_size=5, activation="relu")(ip)
    # x = Pool2d(kernel_size=5)(x)
    # y = Conv2d(number_of_kernel=3, kernel_size=5, activation="relu")(ip)
    # y = Pool2d(kernel_size=5)(y)
    # a = Add(weights_of_layers=[1, 3])([x, y])
    # c = Concat(axis=1)([x, y])
    # f = Flatten()(a)
    x1 = Dense(units=256, activation="sigmoid")(ip)

    # y1 = Dense(units=20, activation="sigmoid")(x1)
    # y2 = Dense(units=20, activation="sigmoid", learning_rate=1)(x1)
    # c1 = Concat(axis=1)([y1, y2])
    #
    # x2 = Dense(units=50, activation="sigmoid", learning_rate=1)(ip)
    # z1 = Dense(units=20, activation="sigmoid", learning_rate=1)(x2)
    # z2 = Dense(units=20, activation="sigmoid", learning_rate=1)(x2)
    # c2 = Concat(axis=1)([z1, z2])

    # c = Concat(axis=1)([c1, c2])
    op = Dense(units=num_class, activation="sigmoid")(x1)

    nn = NeuralNet(ip, op)
    nn.build_model(loss="XE", learning_rate=0.1, batch_size=1)

    weihts_file = os.path.join(save_dir, 'weights.txt')

    if os.path.exists(weihts_file):
        print('Load from ', weihts_file)
        nn.load_weights(filepath=weihts_file)
    else:
        print('download file')
        url = "https://github.com/levopeti/research/blob/neural_network/weights/weights.txt"
        path = download_file(save_dir, url)
        nn.load_weights(filepath=path)


class Input(object):
    def __init__(self, input_size: tuple):
        self.input_size = input_size
        self.output_size = None
        self.batch_size = None

        self.output = None
        self.next_layer = []

    def set_size_forward(self, batch_size, learning_rate):
        self.batch_size = batch_size
        output_size = [batch_size]

        for size in self.input_size:
            output_size.append(size)

        self.output_size = tuple(output_size)

        for layer in self.next_layer:
            layer.set_size_forward(batch_size, learning_rate)

    def set_next_layer(self, layer):
        self.next_layer.append(layer)

    def forward_process(self, x):
        self.output = x
        for layer in self.next_layer:
            layer.forward_process()

    def backward_process(self, input_error):
        # print("input backward")
        # input()
        pass

    def save_weights(self, w_array):
        for layer in self.next_layer:
            layer.save_weights(w_array)

    def load_weights(self, w_array):
        for layer in self.next_layer:
            layer.load_weights(w_array)


class Layer(ABC):
    def __init__(self, activation="sigmoid", learning_rate=None, prev_layer=None):
        self.input_size = None
        self.output_size = None
        self.batch_size = None
        self.learning_rate = learning_rate

        self.act = self.act_func(activation)
        self.d_act = self.d_act_func(activation)

        self.output = None
        self.output_bp = None

        self.W = None
        self.b = None
        self.z = None

        self.prev_layer = prev_layer
        self.next_layer = []

        self.prev_layer_set_next_layer()

        # convention of input shape

    @abstractmethod
    def set_size_forward(self, batch_size, learning_rate):
        pass

    @abstractmethod
    def forward_process(self):
        pass

    @abstractmethod
    def backward_process(self, input_error):
        pass

    @abstractmethod
    def save_weights(self, w_array):
        pass

    @abstractmethod
    def load_weights(self, w_array):
        pass

    def set_next_layer(self, layer):
        self.next_layer.append(layer)

    def prev_layer_set_next_layer(self):
        self.prev_layer.set_next_layer(self)

    def act_func(self, type):
        if type == "tanh":
            return self.tanh

        elif type == "sigmoid":
            return self.log

        elif type == "relu":
            return self.relu

    def d_act_func(self, type):
        if type == "tanh":
            return self.d_tanh

        elif type == "sigmoid":
            return self.d_log

        elif type == "relu":
            return self.d_relu

    @staticmethod
    def tanh(x):
        return np.tanh(x)

    @staticmethod
    def d_tanh(x):
        return 1 - np.tanh(x) ** 2

    @staticmethod
    def log(x):
        return 1 / (1 + np.exp(-1 * x))

    def d_log(self, x):
        return self.log(x) * (1 - self.log(x))

    @staticmethod
    def relu(x):
        return np.maximum(x, 0)

    @staticmethod
    def d_relu(x):
        return np.where(x > 0, 1, 0)


class Dense(Layer):
    def __new__(cls, units, activation="sigmoid", learning_rate=None):
        def set_prev_layer(layer):
            instance = super(Dense, cls).__new__(cls)
            instance.__init__(units, activation=activation, learning_rate=learning_rate, prev_layer=layer)
            return instance
        return set_prev_layer

    def __init__(self, units, activation="sigmoid", learning_rate=None, prev_layer=None):
        super().__init__(activation=activation, learning_rate=learning_rate, prev_layer=prev_layer)
        self.units = units

    def set_size_forward(self, batch_size, learning_rate):
        self.batch_size = batch_size
        self.input_size = self.prev_layer.output_size
        self.output_size = (self.batch_size, 1, self.units)

        if self.learning_rate is None:
            self.learning_rate = learning_rate

        self.W = (np.random.rand(self.input_size[2], self.output_size[2]) * 1) - 0.5
        self.b = (np.random.rand(self.output_size[2]) * 1) - 0.5
        # self.b = np.zeros(self.output_size)

        log = "Dense layer with {} parameters.\nInput size: {}\nOutput size: {}\n".format(self.W.size + self.b.size, self.input_size, self.output_size)
        print(log)

        for layer in self.next_layer:
            layer.set_size_forward(batch_size, learning_rate)

    def save_weights(self, w_array):
        w_array.append(self.W)
        w_array.append(self.b)

        for layer in self.next_layer:
            layer.save_weights(w_array)

    def load_weights(self, w_array):
        assert w_array[0].shape == self.W.shape and w_array[1].shape == self.b.shape

        self.W = w_array[0]
        self.b = w_array[1]

        w_array = w_array[2:]

        for layer in self.next_layer:
            layer.load_weights(w_array)

    def forward_process(self):
        """Fully connected layer forward process."""
        x = self.prev_layer.output
        self.z = np.add(np.dot(x, self.W), self.b)
        self.output = self.act(self.z)

        assert self.output.shape == self.output_size

        for layer in self.next_layer:
            layer.forward_process()

    def backward_process(self, input_error):
        """Fully connected layer backward process"""
        # print("dense backward")
        # TODO: More next layer
        d_act_z = self.d_act(self.z)

        delta_b = np.multiply(input_error, d_act_z)
        x = self.prev_layer.output
        x = np.transpose(x, axes=(0, 2, 1))  # transpose the last two axis

        self.output_bp = np.dot(delta_b, np.transpose(self.W))

        delta_W = np.tensordot(x, delta_b, axes=([0, 2], [0, 1]))
        delta_b = np.sum(delta_b, axis=0).reshape(-1)

        self.W = np.subtract(self.W, delta_W * (self.learning_rate / self.batch_size))
        self.b = np.subtract(self.b, delta_b * (self.learning_rate / self.batch_size))

        assert self.output_bp.shape == self.input_size

        self.prev_layer.backward_process(self.output_bp)


class NeuralNet(object):
    def __init__(self, input, output):
        self.learning_rate = 0.1
        self.loss = None
        self.error = None

        self.X = None
        self.Y = None
        self.Y_am = None        # Y argmax

        self.batch_size = None
        self.num_batches = None
        self.epochs = None

        self.input = input
        self.output = output

        self.model = None

    def __del__(self):
        pass

    def build_model(self, loss="MSE", learning_rate=0.1, batch_size=100):
        print("Build the model...\n")
        self.batch_size = batch_size
        self.learning_rate = learning_rate

        self.learning_rate = learning_rate
        self.loss = self.loss_func(loss)
        self.error = self.error_func(loss)
        self.input.set_size_forward(self.batch_size, self.learning_rate)

    def set_weights(self, individual):
        self.W = np.reshape(np.array(individual[:7840]), (784, 10))  # shape (784, 10)
        self.b = np.array(individual[-10:])  # shape (10,)

    def get_weights_as_genes(self):
        return np.concatenate((np.reshape(self.W, (7840,)), self.b), axis=None)

    def save_weights(self, filepath):
        weights = []
        self.input.save_weights(weights)

        with open(os.path.join(filepath), 'wb') as fp:
            pickle.dump(weights, fp)

    def load_weights(self, filepath):
        with open(os.path.join(filepath), 'rb') as fp:
            weights = pickle.load(fp)

        weights = np.array(weights)
        self.input.load_weights(weights)

    def predict(self, sample):
        """
        sample must have shape (1, 1, -1)
        """
        self.input.forward_process(sample)
        o = self.output.output
        prediction = self.softmax(o)

        return prediction

    def evaluate(self):
        """Evaluate the model."""
        global_loss = 0
        predicted_values = []

        for b in range(self.num_batches):
            # print(b)

            # forward process
            start, end = b * self.batch_size, (b + 1) * self.batch_size
            self.forward(start, end)
            o = self.output.output

            loss, predicted_value = self.loss(o, self.Y[start:end])
            # print(loss)
            # print(predicted_value.shape)
            # exit()
            predicted_values.append(predicted_value)

            global_loss += loss

        predicted_values = np.array(predicted_values).reshape(-1,)

        return global_loss, self.accurate_func(np.array(predicted_values))

    def train_step(self):
        """Train one epoch on the network with backpropagation."""

        for b in range(self.num_batches):
            # print(b)

            # forward
            #start_time = time.time()
            start, end = b * self.batch_size, (b + 1) * self.batch_size
            self.forward(start, end)
            o = self.output.output

            # print("Time of forward: {}s".format(time.time() - start_time))
            error = self.error(o, self.Y[start:end])

            # backward
            #start_time = time.time()
            self.backward(error)
            # print("Time of backward: {}s".format(time.time() - start_time))
            # input()

    def forward(self, start, end):
        self.input.forward_process(self.X[start: end])

    def backward(self, error):
        # for the first layer the output_bp = error
        self.output.backward_process(error)

    def train(self, X, Y, epochs):
        self.X = X
        self.Y = Y
        self.Y_am = np.argmax(Y.reshape(-1, 10), axis=1)

        self.epochs = epochs
        self.num_batches = self.X.shape[0] // self.batch_size

        #print("Start training the model...\n")

        for i in range(self.epochs):
            #start = time.time()
            self.train_step()
            loss_value, accurate = self.evaluate()

            #print("EPOCH", i + 1, "\tAccurate: {0:.2f}%\t".format(accurate * 100), "Loss: {0:.4f}\t".format(loss_value), "Time: {0:.2f}s\n".format(time.time() - start))
            if i == 30:
                self.learning_rate *= 0.5

    def accurate_func(self, pred):
        goal = 0

        for i in range(pred.shape[0]):
            if pred[i] == self.Y_am[i]:         # shape: (70000, 1, 10) --> shape: (70000, 10)
                goal += 1

        return goal / pred.shape[0]

    def loss_func(self, type):
        def mse(o, y):
            return np.square(o - y).sum() * 0.5 / self.batch_size, np.argmax(o, axis=2)

        def xe(o, y):
            prediction = self.softmax(o)
            return self.cross_entropy(prediction, y), np.argmax(prediction, axis=2)

        if type == "MSE":
            return mse

        elif type == "XE":
            return xe

    def error_func(self, type):
        def mse(o, y):
            return np.subtract(o, y)

        def xe(o, y):
            """
            d_cross_entropy
            """
            prediction = self.softmax(o)
            return np.subtract(prediction, y)

        if type == "MSE":
            return mse

        elif type == "XE":
            return xe

    def softmax(self, x):
        """
        Compute softmax values for each sets of scores in x.
        https://deepnotes.io/softmax-crossentropy
        Input and Return shape: (batch size, num of class)
        """
        e_x = np.exp(x - np.max(x, axis=2).reshape(self.batch_size, 1, 1))
        ex_sum = np.sum(e_x, axis=2)
        ex_sum = ex_sum.reshape((self.batch_size, 1, 1))

        return e_x / ex_sum

    @staticmethod
    def cross_entropy(p, y):
        """
        p is the prediction after softmax, shape: (batch size, num of class)
        y is labels (one hot vectors), shape: (batch size, num of class)
        It can be computed as y.argmax(axis=1) from one-hot encoded vectors of labels if required.
        https://deepnotes.io/softmax-crossentropy
        Return size is a scalar.
        cost = -(1.0/m) * np.sum(np.dot(np.log(A), Y.T) + np.dot(np.log(1-A), (1-Y).T))
        """
        # y = y.argmax(axis=1)
        m = y.shape[0]
        #
        # log_likelihood = -np.log(p[range(m), y])
        # loss = np.sum(log_likelihood) / m

        cost = -(1.0 / m) * np.sum(y * np.log(p) + (1 - y) * np.log(1 - p))
        return cost

    @staticmethod
    def d_cross_entropy(p, y):
        """
        p is the prediction after softmax, shape: (batch size, num of class)
        y is labels (one hot vectors), shape: (batch size, num of class)
        Note that y is not one-hot encoded vector.
        It can be computed as y.argmax(axis=1) from one-hot encoded vectors of labels if required.
        https://deepnotes.io/softmax-crossentropy
        Return shape: (batch size, num of class)
        """
        grad = np.subtract(p, y)
        return grad


if __name__ == '__main__':
    RecogApp().run()



