from itsdangerous import BadData
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from django.conf import settings
from . import constants


def check_access_token(access_token_openid):
    '''
    反解,反序列化access_token_openid
    :param access_token_openid: openid密文
    :return: openid明文
    '''
    s = Serializer(settings.SECRET_KEY, constants.ACCESS_TOKEN_EXPIRES)
    # 反序列化openid密文
    try:
        data = s.loads(access_token_openid)
        print(data)
    except BadData:  # openid密文过期
        return None
    else:
        # 返回openid明文
        print(data.get('openid'))
        return data.get('openid')


def generate_access_token(openid):
    '''
    签名，序列化openid
    :param openid: openid明文
    :return: token(openid密文)
    '''
    # 创建序列化器对象
    s = Serializer(settings.SECRET_KEY, constants.ACCESS_TOKEN_EXPIRES)
    # 准备待序列化的字典数据
    data = {'openid': openid}
    # 调用dumps方法进行序列化:类型是bytes
    token = s.dumps(data)
    # 返回序列化后的数据
    return token.decode()
