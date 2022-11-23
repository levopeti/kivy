__version__ = "1.10.1"

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.graphics import Color, Ellipse, Line
# from kivy.core.window import Window
from kivy.properties import NumericProperty, ReferenceListProperty, ObjectProperty, Property
# from kivy.uix.label import Label
#
# from kivy.graphics.texture import Texture
# from kivy.graphics import Rectangle

from abc import ABC, abstractmethod
import numpy as np

import pickle
import os
import PIL
# import time

nn = None
digit_line = []
log = ""


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

    log = Property("")

    def set_pred(self, pred):
        self.current = int(pred)

    def write_log(self, path):
        self.log = str(path)

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
        global digit_line, log

        w = self.parent.width
        h = self.parent.height

        log = ""

        if not nn:
            build_nn('./')

        self.parent.write_log(log)

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
            int_pred.append(int(num * 1000))

        self.parent.draw_prob_rect(int_pred)

    @abstractmethod
    def exit_btn(*kwargs):
        exit()


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


def build_nn(save_dir):
    global nn, log

    num_class = 10

    ip = Input(input_size=(1, 784))
    # x = Conv2d(number_of_kernel=3, kernel_size=5, activation="relu")(ip)
    # x = Pool2d(kernel_size=5)(x)
    # y = Conv2d(number_of_kernel=3, kernel_size=5, activation="relu")(ip)
    # y = Pool2d(kernel_size=5)(y)
    # a = Add(weights_of_layers=[1, 3])([x, y])
    # c = Concat(axis=1)([x, y])
    # f = Flatten()(a)
    x1 = Dense(units=512, activation="sigmoid")(ip)

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
    nn.build_model(loss="XE", optimizer=None, learning_rate=None, batch_size=1)

    weights_file = os.path.join(save_dir, '784_512_10_weights.txt')

    if os.path.exists(weights_file):
        log = 'Load weights from ' + weights_file
        print('Load from ', weights_file)
        nn.load_weights(filepath=weights_file)
    else:
        log = 'No weights found!'
        print('No weights found!')


class Input(object):
    def __init__(self, input_size: tuple):
        self.input_size = input_size
        self.output_size = None
        self.batch_size = None

        self.output = None
        self.next_layer = []

    def set_size_forward(self, batch_size, learning_rate, optimizer):
        self.batch_size = batch_size
        output_size = [batch_size]

        for size in self.input_size:
            output_size.append(size)

        self.output_size = tuple(output_size)

        for layer in self.next_layer:
            layer.set_size_forward(batch_size, learning_rate, optimizer)

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
        self.z_nesterov = None

        # cache for optimizer
        self.cache_W = None
        self.cache_b = None

        self.prev_layer = prev_layer
        self.next_layer = []

        self.prev_layer_set_next_layer()

        self.optimizer = None

    @abstractmethod
    def set_size_forward(self, batch_size, learning_rate, optimizer):
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
        """
        Numerically stable sigmoid function.
        """
        return np.where(x > -1e2, 1 / (1 + np.exp(-x)), 1 / (1 + np.exp(1e2)))

    def d_log(self, x):
        return self.log(x) * (1 - self.log(x))

    @staticmethod
    def relu(x):
        return np.maximum(x, 0)

    @staticmethod
    def d_relu(x):
        return np.where(x > 0, 1, 0)

    def update_weights(self, delta_W, delta_b):
        """Update weights and velocity of the weights."""
        self.W, self.b, self.cache_W, self.cache_b = self.optimizer.run(self.W, self.cache_W, delta_W, self.b, self.cache_b, delta_b, self.learning_rate)


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

    def set_size_forward(self, batch_size, learning_rate, optimizer):
        self.batch_size = batch_size
        self.optimizer = optimizer
        self.input_size = self.prev_layer.output_size
        self.output_size = (self.batch_size, 1, self.units)

        if self.learning_rate is None:
            self.learning_rate = learning_rate

        self.W = (np.random.rand(self.input_size[2], self.output_size[2]) * 1) - 0.5
        self.b = (np.random.rand(self.output_size[2]) * 1) - 0.5

        # self.b = np.zeros(self.output_size)

        # init cache in case nasterov
        # self.cache_W, self.cache_b = self.optimizer.init(self.W.shape, self.b.shape)

        log = "Dense layer with {} parameters.\nInput size: {}\nOutput size: {}\n".format(self.W.size + self.b.size, self.input_size, self.output_size)
        print(log)

        for layer in self.next_layer:
            layer.set_size_forward(batch_size, learning_rate, optimizer)

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

        # if self.optimizer.name == "SGD":
        #     if self.optimizer.nesterov:
        #         nesterov_W = np.subtract(self.W, self.optimizer.gamma * self.cache_W)
        #         nesterov_b = np.subtract(self.b, self.optimizer.gamma * self.cache_b)
        #         self.z_nesterov = np.add(np.dot(x, nesterov_W), nesterov_b)

        self.output = self.act(self.z)

        assert self.output.shape == self.output_size

        for layer in self.next_layer:
            layer.forward_process()

    def backward_process(self, input_error):
        """Fully connected layer backward process"""
        # print("dense backward")

        if self.z_nesterov is not None:
            d_act_z = self.d_act(self.z_nesterov)
        else:
            d_act_z = self.d_act(self.z)

        delta_b = np.multiply(input_error, d_act_z)
        x = self.prev_layer.output

        # transpose the last two axis
        x = np.transpose(x, axes=(0, 2, 1))

        self.output_bp = np.dot(delta_b, np.transpose(self.W))

        delta_W = np.tensordot(x, delta_b, axes=([0, 2], [0, 1]))
        delta_b = np.sum(delta_b, axis=0).reshape(-1)

        # normalization
        delta_W = delta_W / self.batch_size
        delta_b = delta_b / self.batch_size

        self.update_weights(delta_W, delta_b)

        assert self.output_bp.shape == self.input_size

        self.prev_layer.backward_process(self.output_bp)


class NeuralNet(object):
    def __init__(self, input, output):
        self.learning_rate = 0.1
        self.loss = None
        self.error = None
        self.optimizer = None

        self.X = None
        self.Y = None
        self.Y_am = None        # Y argmax

        self.test_x = None
        self.test_y = None
        self.test_y_am = None   # test_y atgmax

        self.batch_size = None
        self.num_batches = None
        self.test_num_batches = None
        self.epochs = None

        self.input = input
        self.output = output

        self.model = None

        self.POOL = True

    def __del__(self):
        pass

    def build_model(self, loss="MSE", optimizer=None, learning_rate=None, batch_size=100):
        print("Build the model...\n")
        self.batch_size = batch_size
        self.learning_rate = learning_rate

        self.loss = self.loss_func(loss)
        self.error = self.error_func(loss)
        self.optimizer = optimizer

        self.input.set_size_forward(self.batch_size, self.learning_rate, self.optimizer)

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

    def evaluate(self, test=False):
        """Evaluate the model."""
        pass

    def train_step(self):
        """Train one epoch on the network with backpropagation."""

        for b in range(self.num_batches):
            # print(b)

            # forward
            # start_time = time.time()
            start, end = b * self.batch_size, (b + 1) * self.batch_size
            self.forward(start, end)

            if self.output.z_nesterov is not None:
                o = self.output.act(self.output.z_nesterov)
            else:
                o = self.output.output

            # print("Time of forward: {}s".format(time.time() - start_time))
            error = self.error(o, self.Y[start:end])

            # backward
            # start_time = time.time()
            self.backward(error)
            # print("Time of backward: {}s".format(time.time() - start_time))
            # input()

    def forward(self, start, end, test=False):
        if not test:
            if end > self.X.shape[0]:
                end = self.X.shape[0]

            self.input.forward_process(self.X[start: end])
        else:
            if end > self.test_x.shape[0]:
                end = self.test_x.shape[0]

            self.input.forward_process(self.test_x[start: end])

    def backward(self, error):
        # for the first layer the output_bp = error
        self.output.backward_process(error)

    def train(self, train_x, train_y, test_x=None, test_y=None, epochs=100):
        pass

    @staticmethod
    def print_stat(i, loss_value, accurate, test_loss_value, test_accurate, train_time, eval_time):
        if test_loss_value:
            # print("EPOCH", i + 1, " Train acc.: {0:.2f}% ".format(accurate * 100), "Train loss: {0:.4f}  ".format(loss_value), "Test acc.: {0:.2f}% ".format(test_accurate * 100), "Test loss: {0:.4f}  ".format(test_loss_value), "Train/eval time: {0:.2f}s/{1:.2f}s\n".format(train_time, eval_time))
            print("EPOCH", i + 1, " Train/eval acc.: {0:.2f}/{1:.2f}% ".format(accurate * 100, test_accurate * 100), "Train/eval loss: {0:.4f}/{1:.4f}  ".format(loss_value, test_loss_value), "Train/eval time: {0:.2f}s/{1:.2f}s\n".format(train_time, eval_time))

        else:
            print("EPOCH", i + 1, "\tTrain accurate: {0:.2f}%\t".format(accurate * 100), "Train loss: {0:.4f}\t".format(loss_value), "Train/eval time: {0:.2f}s/{1:.2f}s\n".format(train_time, eval_time))

    def accurate_func(self, pred, test=False):
        goal = 0

        if not test:
            for i in range(pred.shape[0]):
                if pred[i] == self.Y_am[i]:             # shape: (-1, 1, num_class) --> shape: (-1, num_class)
                    goal += 1
        else:
            for i in range(pred.shape[0]):
                if pred[i] == self.test_y_am[i]:
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

        # batch_size
        m = y.shape[0]

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



