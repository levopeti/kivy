import kivy
kivy.require('1.10.1')

from kivy.app import App
from kivy.uix.button import Button


import thread
import time
from pytube import YouTube


class MyApp(App):

    def download_file(self, url):
        save_dir = self.user_data_dir
        save_dir = "/home/biot"
        local_filename = url.split('/')[-1]
        local_file = os.path.join(save_dir, local_filename)

        def open_pickle(req, result):
            # weights = pickle.load(result)
            print(req)
            print(type(result))

        response = UrlRequest(url + "?raw=true", open_pickle)
        # response = urlopen(url + "?raw=true")
        print(response.result)
        # CHUNK = 16 * 1024
        #
        # with open(local_file, 'wb') as f:
        #     while True:
        #         chunk = response.result.read(CHUNK)
        #         if not chunk:
        #             break
        #         f.write(chunk)

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

    def download(self, button):

        url = "https://www.youtube.com/watch?v=g1j3O8NYGRE"
        yt = YouTube(url)
        print(yt.tile)
        stream = yt.streams.filter(only_audio=True).first()
        stream.download('/Download')

    def build(self):
        return Button(text='Download', on_press=self.download)


if __name__ == '__main__':
    MyApp().run()