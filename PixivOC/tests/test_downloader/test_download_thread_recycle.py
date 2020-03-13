import time
from Download import *


def main():
    package = RequestPackage('https://www.baidu.com/img/bd_logo1.png', 'GET')
    download_thread = DownloadThread(lambda x: print('processing return value'))
    download_thread.start(lambda x: print('return loop value'), [package])
    while True:
        time.sleep(1)
        print(download_thread.is_alive())


main()
