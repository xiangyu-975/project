from fdfs_client.client import Fdfs_client

client = Fdfs_client('./fastdfs/client.conf')

ret = client.upload_by_filename(r'./kk')
print(ret)
