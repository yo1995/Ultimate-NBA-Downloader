# -*- coding:utf-8 -*-

__author__ = 'cht'
'''
Bleacher Report NBA photo downloader

thoughts: 
- 尝试threading 调用以增强网络访问速度，同时不占用过多系统资源
- 尝试multiprocess 调用以增强io密集型函数的速度
credits:
- http://python.jobbole.com/86822/
- https://segmentfault.com/a/1190000007495352
- https://www.cnblogs.com/lilinwei340/p/6793796.html
- https://www.cnblogs.com/Thkeer/p/5559814.html
- [map]https://stackoverflow.com/questions/26520781/multiprocessing-pool-whats-the-difference-between-map-async-and-imap
- https://www.cnblogs.com/hujq1029/p/7219163.html
# process
- https://blog.csdn.net/midorra/article/details/52413659
- https://my.oschina.net/abcfy2/blog/305159
- https://www.coder4.com/archives/3352
- http://www.jb51.net/article/127354.htm
- https://www.jianshu.com/p/1f63fa9d1c20
- https://blog.csdn.net/dutsoft/article/details/54694798
- [no import]https://docs.python.org/3/library/multiprocessing.html
concerns:
- [no interrupt]https://bugs.python.org/issue8296
- https://stackoverflow.com/questions/1408356/keyboard-interrupts-with-pythons-multiprocessing-pool
- https://stackoverflow.com/questions/38271547/when-should-we-call-multiprocessing-pool-join
- [join over activeCount]https://stackoverflow.com/questions/20575746/python-and-ipython-threading-activecount
'''

import threading
import logging
log = logging.getLogger(__name__)


class MyThread(threading.Thread):

    def __init__(self, func, args=()):
        super(MyThread, self).__init__()
        self.func = func
        self.args = args
        self.result = []

    def run(self):
        self.result = self.func(*self.args)  # *self.args for changeable length

    def get_result(self):
        return self.result
        # try:
        #     return self.result  # 如果子线程不使用join方法，此处可能会报没有self.result的错误
        # except Exception:
        #     return None



