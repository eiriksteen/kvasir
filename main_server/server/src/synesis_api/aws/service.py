from requests.exceptions import HTTPError
from synesis_api.aws.config import s3_client, ec2_client, efs_client


def create_security_group():
    pass


def create_vpc():
    pass


def create_efs_system():
    pass


def create_ec2_instance():
    pass


def mount_efs_on_ec2_instance():
    pass


def upload_object_s3(obj: object, bucket_name: str, file_key: str):
    try:
        s3_client.put_object(Body=obj.model_dump_json(),
                             Bucket=bucket_name, Key=file_key)
    except:
        raise HTTPError(status_code=500,
                        detail="Failed to upload object to S3.")


def retrieve_object_s3(bucket_name: str, file_key: str):
    response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
    json_data = response["Body"].read().decode("UTF-8")
    return json_data


# Global AWS now dealt with using cloudformation
# class SetupGlobalAWS:
#     """
#     Sets up VPC, EFS (primarily for storing code), and security groups for main server, project servers, DB, Redis, Task IQ.
#     Then sets up S3 for storing data.
#     """


class SetupProjectEC2:
    """
    Sets up EC2 instance and mounts EFS on EC2 instance for a specific project. Security group to only allow access from main server.
    """
