import os
import json
from flask import Blueprint, request, jsonify
import boto3
import botocore
from datetime import datetime
import time

# Set up blueprint to which prefix will be applied
api = Blueprint("api", __name__)

# AWS S3 Bucket Connection Set Up
s3 = boto3.client("s3", aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"), aws_secret_access_key=os.environ.get(
    "AWS_SECRET_ACCESS_KEY"), region_name="us-east-1")  # access keys are private so they should never be available to the public
db = boto3.client("dynamodb", aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
                  aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"), region_name="us-east-1")
auth = boto3.client("cognito-idp", aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
                    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"), region_name="us-east-1")
ecoder = boto3.client("elastictranscoder", aws_access_key_id=os.environ.get(
    "AWS_ACCESS_KEY_ID"), aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"), region_name="us-east-1")

# s3 methods require you to provide the bucket name every time so we store it for efficiency
BUCKET_NAME = "visual-media-bucket"
COMPRESS_BUCKET_NAME = "processed-media-gamingforum"
AWS_REGION = "us-east-1"  # some methods require region to be specify


def get_S3_object_url(bucket_name, key):
    
    return f"https://{bucket_name}.s3.amazonaws.com/{key.replace(' ', '+')}"

# Get a welcoming message once you start the server.


@api.route('/')
def home():
    return 'Home sweet home! <strong> Your Yoga App! | THIS IS IT | <strong>'


@api.route("/buckets")
def get_all_buckets():
    buckets_resp = s3.list_buckets()

    # response has a buckets key which is an array, if the array has more than 0 elements, then that means there are exisiting buckets
    if len(buckets_resp["Buckets"]) > 0:
        return jsonify(buckets_resp), 200

    return jsonify("No S3 buckets found!"), 200


@api.route("/table", methods=["POST"])
@api.route("/bucket/objects")
def get_all_objects_in_bucket():
    response = s3.list_objects_v2(Bucket=BUCKET_NAME)

    if response["KeyCount"] > 0:
        # NOTE the statement below is used to filter an s3 bucket for all files of type mp4, changing .mp4 with something else will filter for that other thing
        # list(filter(lambda file: file["Key"].endswith(".mp4") , response["Contents"]))

        return jsonify(response), 200

    return jsonify(f"No objects in the bucket {BUCKET_NAME}"), 200


@api.route("/bucket/upload", methods=["POST"])
def upload_file():
    # get the files that we submit from the front-end
    img = request.files.get("image")
    video = request.files.get("video")
    audio = request.files.get("audio")

    f = open("output.json", "w")
    f.write(str(video.content_type))
    f.close()

    response = {}

    # if img is not None:
    #     s3.upload_fileobj(img, BUCKET_NAME, img.filename,
    #                       ExtraArgs={"ACL": "public-read"})
    #     response["imgURL"] = get_S3_object_url(COMPRESS_BUCKET_NAME, img.filename)
    # if video is not None:
    #     s3.upload_fileobj(video, BUCKET_NAME, video.filename,
    #                       ExtraArgs={"ACL": "public-read"})
    #     response["videoURL"] = get_S3_object_url( COMPRESS_BUCKET_NAME, video.filename)


    #     print(response)
    # if audio is not None:
    #     s3.upload_fileobj(audio, BUCKET_NAME, audio.filename,
    #                       ExtraArgs={"ACL": "public-read"})
    #     response["audioURL"] = get_S3_object_url( COMPRESS_BUCKET_NAME, audio.filename)

    return jsonify(response), 200


# AUTH USER

@api.route("/auth/signup", methods=["POST"])
def create_user_account():
    request_body = request.get_json(force=True)

    email = request_body["email"]
    username = request_body["username"]
    name = request_body["name"]
    password = request_body["password"]
    age = request_body["age"]

    # Create a datetime object representing the current time
    now = datetime.now()

    # Convert the datetime object to a Unix timestamp
    unix_timestamp = int(time.mktime(now.timetuple()))

    print(unix_timestamp)

    try:
        aws_auth_res = auth.sign_up(
            ClientId=os.environ.get("AWS_COGNITO_CLIENT_ID"),
            Username=username,
            Password=password,
            UserAttributes=[
                {
                    "Name": "email",
                    "Value": email
                },
                {
                    "Name": "custom:age",
                    "Value": str(age)
                },
                {
                    "Name": "name",
                    "Value": name
                },
                {
                    "Name": "updated_at",
                    "Value": str(unix_timestamp)
                },

            ]
        )
    except (botocore.exceptions.ClientError) as err:
        error_code = err.response["Error"]['Code']
        if error_code == 'InvalidPasswordException':
            return jsonify("Invalid password!"), 400

        if error_code == 'UsernameExistsException':
            return jsonify("User already exits!"), 400

        print("Summary:", error_code)
        print("Details:", err)

        return jsonify("Something went wrong"), 400

    return jsonify(aws_auth_res)


@api.route("/auth/verify-account", methods=["POST"])
def confirm_registration():
    request_body = request.get_json(force=True)

    code = request_body["confirmation_code"]
    username = request_body["username"]

    try:
        aws_auth_res = auth.confirm_sign_up(
            ClientId=os.environ.get("AWS_COGNITO_CLIENT_ID"),
            Username=username,
            ConfirmationCode=code
        )
    except Exception as e:
        print(e)

        return jsonify("Something went wrong! Try again later."), 400

    print(aws_auth_res)

    return jsonify(aws_auth_res)


@api.route("/auth/login", methods=["POST"])
def signin_user_account():
    request_body = request.get_json(force=True)

    username = request_body["username"] if "username" in request_body else request_body["email"]
    password = request_body["password"]

    try:
        aws_auth_res = auth.initiate_auth(
            ClientId=os.environ.get("AWS_COGNITO_CLIENT_ID"),
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password
            }
        )
    except (botocore.exceptions.ClientError) as err:
        error_code = err.response["Error"]['Code']
        if error_code == 'InvalidPasswordException':
            return jsonify("Invalid password!"), 400

        print("Summary:", error_code)
        print("Details:", err)

        return jsonify("Something went wrong"), 400

    return jsonify(aws_auth_res)

@api.route("/auth/user/data", methods=["GET"])
def get_user_data():
    bearer_token = request.headers.get("Authorization")
    
    if bearer_token is not None:
        token=bearer_token.split()[-1]

    try:
        aws_auth_res = auth.get_user(
            AccessToken=token
        )
    except (botocore.exceptions.ClientError) as err:
        error_code = err.response["Error"]['Code']
        if error_code == 'InvalidPasswordException':
            return jsonify("Invalid password!"), 401

        print("Summary:", error_code)
        print("Details:", err)

        return jsonify("Token is not valid "), 401

    return jsonify(aws_auth_res)


@api.route("/db/public/videos", methods=["GET"])
def get_all_videos():
    response = db.scan(
        TableName="serenity_videos",
        Limit=20,
        Select="ALL_ATTRIBUTES"
    )

    comments = response["Items"][0]["comments"]["SS"]

    # turns comment strings into proper dictionaries
    for index, comment in enumerate(comments):
        comments[index] = json.loads(comment)


    return jsonify(response), 200
