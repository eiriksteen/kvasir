from requests.exceptions import HTTPError
from asgiref.sync import sync_to_async
from synesis_api.aws.s3_auth import client


@sync_to_async
def upload_object_s3(obj: object, bucket_name: str, file_key: str):
    try:
        client.put_object(Body=obj.model_dump_json(),
                          Bucket=bucket_name, Key=file_key)
    except:
        raise HTTPError(status_code=500,
                        detail="Failed to upload object to S3.")


@sync_to_async
def retrieve_object(bucket_name: str, file_key: str):
    response = client.get_object(Bucket=bucket_name, Key=file_key)
    json_data = response["Body"].read().decode("UTF-8")
    return json_data
