import logging
import os
import threading
import dotenv
import requests
from botocore.exceptions import ClientError
import datetime
from datetime import datetime, timezone
import fileDeleteTimer

dotenv.load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class S3Client:
    def __init__(self):
        self.endpoint_url = os.getenv("S3_URL")
        self.access_key = os.getenv("S3_ACCESS_KEY")
        self.secret_key = os.getenv("S3_SECRET_KEY")
        self.bucket_name = os.getenv("S3_BUCKIT_NAME")

        # Используем boto3 для операций со списком и удалением
        import boto3
        from botocore.client import Config

        self.boto3_session = boto3.Session(
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
        )

        self.s3_client = self.boto3_session.client(
            "s3",
            endpoint_url=self.endpoint_url,
            config=Config(
                signature_version="s3v4",
                s3={"addressing_style": "path"},
            ),
        )

    def get_file_size(self, file_path):
        """Получить размер файла в байтах"""
        try:
            size = os.path.getsize(file_path)
            logger.info(f"Размер файла {file_path}: {size} байт ({self._format_size(size)})")
            return size
        except OSError as e:
            logger.error(f"Не удалось получить размер файла: {e}")
            return None

    def _format_size(self, size_bytes):
        """Форматировать размер в человекочитаемый вид"""
        for unit in ['Б', 'КБ', 'МБ', 'ГБ']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} ТБ"
    
    
    def upload_file(self, bucket_name, file_path, object_name=None):
        """Загрузка файла через прямой PUT-запрос"""
        if object_name is None:
            object_name = os.path.basename(file_path)

        # Читаем содержимое файла
        with open(file_path, "rb") as f:
            file_content = f.read()

        if not self.get_file_size(file_path) > 4000 * 1024:    
            try:
                # Создаём временную ссылку
                presigned_url = self.s3_client.generate_presigned_url(
                    "put_object",
                    Params={
                        "Bucket": bucket_name,
                        "Key": object_name,
                        "ContentType": "application/octet-stream",
                    },
                    ExpiresIn=3600,
                    HttpMethod="PUT",
                )

                # Загружаем через requests по временной ссылке
                response = requests.put(
                    presigned_url,
                    data=file_content,
                    headers={"Content-Type": "application/octet-stream"},
                )

                if response.status_code == 200:
                    logger.info(f"Файл {file_path} загружен как {object_name}")

                    # Получаем код состояния
                    head_response = self.s3_client.head_object(
                        Bucket=bucket_name, Key=object_name
                    )
                    return head_response["ResponseMetadata"]["HTTPStatusCode"]
                else:
                    raise Exception(
                        f"Загрузка не удалась, статус {response.status_code}: {response.text}"
                    )

            except Exception as e:
                logger.error(f"Загрузка не удалась: {e}")
                raise
        else:
            logger.warning(f"Файл {file_path} слишком большой для прямой загрузки, пропущен")
            return 124  # Специальный код для слишком больших файлов

    def get_all_files(self, bucket_name):
        """Список всех файлов в хранилище"""
        try:
            response = self.s3_client.list_objects_v2(Bucket=bucket_name)
            if "Contents" in response:
                return [obj["Key"] for obj in response["Contents"]]
            return []
        except ClientError as e:
            logger.error(f"Не удалось получить список файлов: {e}")
            return []

    def download_file(self, bucket_name, object_name, file_path):
        """Скачать файл из облачного хранилища"""
        try:
            self.s3_client.download_file(bucket_name, object_name, file_path)
            logger.info(f"Файл {object_name} скачан в {file_path}")
            return True
        except ClientError as e:
            logger.error(f"Скачивание не удалось: {e}")
            raise

    def delete_file(self, bucket_name, object_name):
        """Удалить файл из облачного хранилища"""
        try:
            self.s3_client.delete_object(Bucket=bucket_name, Key=object_name)
            logger.info(f"Файл {object_name} удалён из хранилища {bucket_name}")
            return True
        except ClientError as e:
            logger.error(f"Удаление не удалось: {e}")
            raise

    def file_exists(self, bucket_name, object_name):
        """Проверить, существует ли файл в хранилище"""
        try:
            self.s3_client.head_object(Bucket=bucket_name, Key=object_name)
            return True
        except ClientError:
            return False

    def bucket_exists(self, bucket_name):
        """Проверить, существует ли папка"""
        try:
            self.s3_client.head_bucket(Bucket=bucket_name)
            return True
        except ClientError:
            return False

    def create_bucket(self, bucket_name):
        """Создать новую папку"""
        try:
            self.s3_client.create_bucket(Bucket=bucket_name)
            logger.info(f"Папка {bucket_name} успешно создана")
            return True
        except ClientError as e:
            logger.error(f"Не удалось создать папку: {e}")
            raise

    def get_object_metadata(self, bucket_name, object_name):
        """Получить метаданные файла"""
        try:
            response = self.s3_client.head_object(Bucket=bucket_name, Key=object_name)
            return {
                "size": response["ContentLength"],
                "last_modified": response["LastModified"],
                "content_type": response.get("ContentType", "unknown"),
                "etag": response.get("ETag", ""),
            }
        except ClientError as e:
            logger.error(f"Не удалось получить метаданные: {e}")
            return None

    def get_download_url(self, bucket_name, object_name, expires_in=3600):
        """Создать временную ссылку для скачивания файла"""
        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": bucket_name,
                    "Key": object_name,
                },
                ExpiresIn=expires_in,
            )
            return url
        except ClientError as e:
            logger.error(f"Не удалось создать временную ссылку: {e}")
            return None

    def get_download_url_with_name(
        self, bucket_name, object_name, filename, expires_in=3600
    ):
        """Создать временную ссылку для скачивания с указанием имени файла."""
        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": bucket_name,
                    "Key": object_name,
                    "ResponseContentDisposition": f'attachment; filename="{filename}"',
                },
                ExpiresIn=expires_in,
            )
            return url
        except ClientError as e:
            logger.error(f"Не удалось создать временную ссылку: {e}")
            return None

    def get_file_existing_time(self, bucket_name, object_name):
        """Получить время существования файла в секундах"""
        try:
            response = self.s3_client.head_object(Bucket=bucket_name, Key=object_name)
            last_modified = response["LastModified"]
            current_time = datetime.now(timezone.utc)
            existing_time = (current_time - last_modified).total_seconds()
            return existing_time
        except ClientError as e:
            logger.error(f"Не удалось получить время существования: {e}")
            return None

# Создаём синглтон-клиент
s3_client = S3Client()


# Упрощённые функции для обратной совместимости
def upload_file(bucket_name, file_path, object_name=None):
    return s3_client.upload_file(bucket_name, file_path, object_name)


def get_all_files(bucket_name):
    return s3_client.get_all_files(bucket_name)


def download_file(bucket_name, object_name, file_path):
    return s3_client.download_file(bucket_name, object_name, file_path)


def delete_file(bucket_name, object_name):
    return s3_client.delete_file(bucket_name, object_name)


def file_exists(bucket_name, object_name):
    return s3_client.file_exists(bucket_name, object_name)


def bucket_exists(bucket_name):
    return s3_client.bucket_exists(bucket_name)


def create_bucket(bucket_name):
    return s3_client.create_bucket(bucket_name)


def get_object_metadata(bucket_name, object_name):
    return s3_client.get_object_metadata(bucket_name, object_name)


def get_download_url(bucket_name, object_name):
    return s3_client.get_download_url(bucket_name, object_name)


def get_download_url_with_name(bucket_name, object_name, filename):
    return s3_client.get_download_url_with_name(bucket_name, object_name, filename)


if __name__ == "__main__":
    # Проверка подключения
    bucket_name = os.getenv("S3_BUCKIT_NAME")

    threading.Thread(target=fileDeleteTimer.delete_old_files, args=(bucket_name, 7)).start()  # Запускаем удаление старых файлов в отдельном потоке
    
    
    if bucket_name:
        print(f"Проверка подключения к облачному хранилищу...")
        print(f"Адрес: {s3_client.endpoint_url}")
        print(f"Папка: {bucket_name}")

        if s3_client.bucket_exists(bucket_name):
            print(f"✓ Папка '{bucket_name}' существует")

            files = s3_client.get_all_files(bucket_name)
            print(f"✓ Найдено {len(files)} файлов в хранилище")
            for file in files[:5]:
                print(f"  - {file}")
        else:
            print(f"✗ Папка '{bucket_name}' не существует")
    else:
        print("✗ S3_BUCKIT_NAME не указан в .env файле")
