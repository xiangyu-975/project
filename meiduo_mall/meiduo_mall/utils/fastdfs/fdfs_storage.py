from django.conf import settings
from django.core.files.storage import Storage


class FastDFSStorage(Storage):
    '''自定义文件的存储类'''

    # 文件存储类的初始化方法
    def __init__(self, fdfs_base_url=None):
        # if not fdfs_base_url:
        #     self.fdfs_base_url = settings.FDFS_BASE_URL
        # self.fdfs_base_url = fdfs_base_url
        self.fdfs_base_url = fdfs_base_url or settings.FDFS_BASE_URL

    def _open(self, name, mode='rb'):
        '''打开文件时会被调用的：必须重写'''
        # 因为当前不是去打开某一个文件，所以这个方法目前无用，但是有必须重写，所以pass，做文件的下载
        pass

    def _save(self, name, content):
        '''
        PS：将来在后台管理系统中，需要在这个方法中实现文件上传到FDFS服务器
        保存文件时会被调用的：文档告诉我必须重写
        :param name: 文件路径
        :param content: 文件二进制内容
        :return: None
        '''

        # 因为当前不是去保存文件，所以这个方法目前无用，必须重写
        pass

    def url(self, name):
        '''
        返回文件的全路径
        :param name: 文件的相对路径
        :return: http://192.168.103.158:8888/group1/M00/00/00/wKhnnlxw_gmAcoWmAAEXU5wmjPs35.jpeg
        '''
        # return 'http://192.168.220.128:8888/' + name
        return self.fdfs_base_url + name
