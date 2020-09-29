import logging
from django.core.mail import send_mail
from django.conf import settings
from celery_tasks.main import celery_app

logger = logging.getLogger('django')


@celery_app.task(name='send_verify_email')
def send_verify_email(self, to_email, verify_url):
    '''定义发送验证邮件的任务'''
    # send_mail('标题','普通邮件正文','收件人列表','符文本邮件正文(html)')
    subject = '美多商城邮箱验证'
    html_message = '<p>尊敬的用户你好！</p>' \
                   '<p>感谢你使用美多商城。</p>' \
                   '<p>您的邮箱为：%s 。请点击此链接激活您的邮箱：</p>' \
                   '<p><a href="%s">%s<a></p>' % (to_email, verify_url, verify_url)
    try:
        send_mail(subject, '', settings.EMAIL_FROM, [to_email], html_message=html_message)
    except Exception as e:
        logger.error(e)
        # 有异常自动重试三次
        raise self.retry(exc=e, max_retries=3)
