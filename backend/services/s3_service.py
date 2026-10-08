import boto3
import os

class S3Service:
    def __init__(self):
        self.region_name = os.getenv("AWS_REGION")
        self.bucket_name = os.getenv("S3_BUCKET_NAME")
        if self.region_name and self.bucket_name:
            self.client = boto3.client("s3", region_name=self.region_name)
        else:
            self.client = None

    def upload_file(self, file_path: str, object_name: str) -> bool:
        if not self.client:
            return False
        try:
            self.client.upload_file(file_path, self.bucket_name, object_name)
            return True
        except Exception as e:
            print(f"S3 upload error: {e}")
            return False
            
    def delete_file(self, object_name: str) -> bool:
        if not self.client:
            return False
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=object_name)
            return True
        except Exception as e:
            print(f"S3 delete error: {e}")
            return False
