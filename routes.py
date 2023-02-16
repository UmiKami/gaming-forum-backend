import os
from flask import Blueprint, request, jsonify
import boto3

# Set up blueprint to which prefix will be applied
api = Blueprint("api", __name__)

# AWS S3 Bucket Connection Set Up
s3 = boto3.client("s3", aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"), aws_secret_access_key= os.environ.get("AWS_SECRET_ACCESS_KEY") ) # access keys are private so they should never be available to the public

BUCKET_NAME = "visual-media-bucket" # s3 methods require you to provide the bucket name every time so we store it for efficiency
AWS_REGION = "us-east-1" # some methods require region to be specify

def get_S3_object_url(bucket_name, key):
    return f"https://{bucket_name}.s3.amazonaws.com/{key.replace(' ', '+')}"

# Get a welcoming message once you start the server.
@api.route('/')
def home():
    return 'Home sweet home! <strong> Your Gaming Forum App! <strong>'

@api.route("/buckets")
def get_all_buckets():
    buckets_resp = s3.list_buckets()

    # response has a buckets key which is an array, if the array has more than 0 elements, then that means there are exisiting buckets
    if len(buckets_resp["Buckets"]) > 0:
        return jsonify(buckets_resp), 200
    
    return jsonify("No S3 buckets found!"), 200

@api.route("/bucket/objects")
def get_all_objects_in_bucket():
    response = s3.list_objects_v2(Bucket=BUCKET_NAME)

    if response["KeyCount"] > 0:
        # NOTE the statement below is used to filter an s3 bucket for all files of type mp4, changing .mp4 with something else will filter for that other thing
        # list(filter(lambda file: file["Key"].endswith(".mp4") , response["Contents"])) 

        return jsonify(), 200
    
    return jsonify(f"No objects in the bucket {BUCKET_NAME}"), 200

@api.route("/bucket/upload", methods=["POST"])
def upload_file():
    # get the files that we submit from the front-end 
    img = request.files.get("image")
    video = request.files.get("video")
    audio = request.files.get("audio")

    response = {}

    if img is not None:
        s3.upload_fileobj(img, BUCKET_NAME, img.filename, ExtraArgs={"ACL":"public-read"})
        response["imgURL"] =get_S3_object_url(AWS_REGION,BUCKET_NAME, img.filename)
    if video is not None:
        s3.upload_fileobj(video, BUCKET_NAME, video.filename, ExtraArgs={"ACL":"public-read"})
        response["videoURL"] =get_S3_object_url(AWS_REGION,BUCKET_NAME, video.filename)
    if audio is not None:
        s3.upload_fileobj(audio, BUCKET_NAME, audio.filename, ExtraArgs={"ACL":"public-read"})
        response["audioURL"] = get_S3_object_url(AWS_REGION,BUCKET_NAME, audio.filename)
    
    
    return jsonify(response), 200