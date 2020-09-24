# coding=gbk

# coding=utf-8

# -*- coding: UTF-8 -*-

from verifications.libs.yuntongxun.CCPRestSDK import REST

# ˵�������˺ţ���½��ͨѶ��վ�󣬿���"����̨-Ӧ��"�п������������˺�ACCOUNT SID
_accountSid = '8a216da86d05dc0b016d4df574c32f95'

# ˵�������˺�Token����½��ͨѶ��վ�󣬿��ڿ���̨-Ӧ���п������������˺�AUTH TOKEN
_accountToken = '91be773d51774eda94f3382c25fb1124'

# ��ʹ�ù������̨��ҳ��APPID���Լ�����Ӧ�õ�APPID
_appId = '8aaf070874af41ee0174ba6671f205cc'

# ˵���������ַ�������������ó�app.cloopen.com
_serverIP = 'sandboxapp.cloopen.com'

# ˵��������˿� ����������Ϊ8883
_serverPort = "8883"

# ˵����REST API�汾�ű��ֲ���
_softVersion = '2013-12-26'


# ��ͨѶ�ٷ��ṩ�ķ��Ͷ��Ŵ���ʵ��


# ����ģ�����
# @param to �ֻ�����
# @param datas �������� ��ʽΪ���� ���磺{'12','34'}���粻���滻���� ''
# @param $tempId ģ��Id

# def sendTemplateSMS(to, datas, tempId):
#     # ��ʼ��REST SDK
#     rest = REST(_serverIP, _serverPort, _softVersion)
#     rest.setAccount(_accountSid, _accountToken)
#     rest.setAppId(_appId)
#
#     result = rest.sendTemplateSMS(to, datas, tempId)
#     print(result)


class CCP(object):
    '''���Ͷ��ŵĵ�����'''

    def __new__(cls, *args, **kwargs):
        '''
        ���嵥���ĳ�ʼ������
        :return: ����
        '''
        # �жϵ����Ƿ����:_instance �����д洢�ľ��ǵ���
        if not hasattr(cls, '_instance'):
            # ������������ڣ���ʼ������
            cls._instance = super(CCP, cls).__new__(cls, *args, **kwargs)
            # ��ʼ��REST SDK
            cls._instance.rest = REST(_serverIP, _serverPort, _softVersion)
            cls._instance.rest.setAccount(_accountSid, _accountToken)
            cls._instance.rest.setAppId(_appId)
        # ���ص���
        return cls._instance
        # for k, v in result.iteritems():
        #
        #     if k == 'templateSMS':
        #         for k, s in v.iteritems():
        #             print('%s:%s' % (k, s))
        #     else:
        #         print('%s:%s' % (k, v))

    def send_template_sms(self, to, datas, tempId):
        '''
        ���Ͷ�����֤�뵥������
        :param to: �ֻ�����
        :param datas: ��������
        :param tempId: ģ��ID
        :return: �ɹ���0��ʧ�ܣ�-1
        '''
        result = self._instance.rest.sendTemplateSMS(to, datas, tempId)
        print(result)
        if result.get('statusCode') == '000000':
            return 0
        else:
            return -1


# sendTemplateSMS(�ֻ�����,��������,ģ��Id)
if __name__ == '__main__':
    # ע�⣺���Զ���ģ����Ϊ1
    # sendTemplateSMS('13337717632', ['123456', 5], 1)
    # �����෢�Ͷ�����֤��
    CCP().send_template_sms('13337717632', ['123456', 5], 1)
