# Imports necessary libraries
import os
from flask import Flask, jsonify, request
from flask_cors import CORS
import boto3

# Set Up AWS S3

BUCKET_NAME = "visual-media-bucket"
AWS_REGION = "us-east-1"

s3 = boto3.client("s3", aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"), aws_secret_access_key= os.environ.get("AWS_SECRET_ACCESS_KEY") )

# Define the app
app = Flask(__name__)
CORS(app, resources={r"*": {"origins": "*"}})

def get_S3_object_url(region, bucket_name, key):
    return f"https://{bucket_name}.s3.amazonaws.com/{key.replace(' ', '+')}"

# Get a welcoming message once you start the server.
@app.route('/')
def home():
    return 'Home sweet home! <strong> Changed!<strong>'

@app.route("/buckets")
def get_all_buckets():
    buckets_resp = s3.list_buckets()

    if len(buckets_resp["Buckets"]) > 0:
        return jsonify(buckets_resp), 200
    
    return jsonify("No S3 buckets found!"), 200

@app.route("/bucket/objects")
def get_all_objects_in_bucket():
    response = s3.list_objects_v2(Bucket=BUCKET_NAME)

    if response["KeyCount"] > 0:
        return jsonify(list(filter(lambda file: file["Key"].endswith(".mp4") , response["Contents"]))), 200
    
    return jsonify(f"No objects in the bucket {BUCKET_NAME}"), 200

@app.route("/bucket/upload", methods=["POST"])
def upload_file():
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
    

    # if response["KeyCount"] > 0:
    #     return jsonify(response["Contents"]), 200
    
    return jsonify(response), 200






# If the file is run directly,start the app.
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=True)

# To execute, run the file. Then go to 127.0.0.1:5000 in your browser and look at a welcoming message.