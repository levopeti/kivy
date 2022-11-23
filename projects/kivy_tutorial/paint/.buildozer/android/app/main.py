__version__ = "0.7"

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.graphics import Color, Ellipse, Line
import numpy as np


class MyPaintWidget(Widget):
    def on_touch_down(self, touch):
        with self.canvas:
            x = np.random.rand(100, 100)
            y = np.random.rand(100, 100)
            z = np.dot(x, y)
            r = np.random.rand()
            g = np.random.rand()
            b = np.random.rand()
            Color(r, g, b)
            d = np.random.rand() * 50
            Ellipse(pos=(touch.x - d / 2, touch.y - d / 2), size=(d, d))
            touch.ud['line'] = Line(points=(touch.x, touch.y))

    def on_touch_move(self, touch):
        touch.ud['line'].points += [touch.x, touch.y]


class MyPaintApp(App):
    def build(self):
        parent = Widget()
        self.painter = MyPaintWidget()
        clearbtn = Button(text='Clear')
        clearbtn.bind(on_release=self.clear_canvas)
        parent.add_widget(self.painter)
        parent.add_widget(clearbtn)
        return parent

    def clear_canvas(self, obj):
        self.painter.canvas.clear()


if __name__ == '__main__':
    MyPaintApp().run()



