import s3
import logging
from botocore.exceptions import ClientError
import datetime
from datetime import datetime, timezone
import time


logger = logging.getLogger(__name__)


def delete_old_files(bucket_name, days_old=7):
    """Удаляет файлы из S3, которые старше указанного количества дней"""
    s3_client = s3.get_s3_client()
    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        if 'Contents' in response:
            now = datetime.now(timezone.utc)
            for obj in response['Contents']:
                last_modified = obj['LastModified']
                age = (now - last_modified).days
                if age > days_old:
                    logger.info(f"Удаление файла {obj['Key']} (возраст {age} дней)")
                    s3_client.delete_object(Bucket=bucket_name, Key=obj['Key'])
    except ClientError as e:
        logger.error(f"Ошибка при удалении файлов: {e}")