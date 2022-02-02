#!/usr/bin/env python3

#Source https://github.com/GoogleCloudPlatform/python-docs-samples/blob/db182f77a0d29dd1ee6e20516d96db8b3b72684e/iot/api-client/http_example/cloudiot_http_example.py

# [START iot_http_includes]
import argparse
import base64
import datetime
import json
import time

from google.api_core import retry
import jwt
import requests

registry_id = "registry_id"
cloud_region = "cloud_region"
project_id = "project_id"
device_id = "jetson-nano"
message_type = "event"
algorithm = "RS256"
private_key_file = "path_here/rsa_private.pem"
base_url = "https://cloudiotdevice.googleapis.com/v1"
_BACKOFF_DURATION = 60


def converter(text):
    #parse argument to variables 
    a_dict = {}
    bus_count, date_day, time_in_sec = text.split(",")
    bus_number = bus_count
    date = date_day
    time = time_in_sec
    for variable in ["bus_number", "date", "time"]:
        a_dict[variable] = eval(variable)
    message = json.dumps(a_dict)
    print("sending the message ", message)
    return message

# [START iot_http_jwt]
def create_jwt(project_id, private_key_file, algorithm):
    token = {
        # The time the token was issued.
        "iat": datetime.datetime.now(tz=datetime.timezone.utc),
        # Token expiration time.
        "exp": datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(minutes=60),
        # The audience field should always be set to the GCP project id.
        "aud": project_id,
    }

    # Read the private key file.
    with open(private_key_file, "r") as f:
        private_key = f.read()

    print(
        "Creating JWT using {} from private key file {}".format(
            algorithm, private_key_file
        )
    )

    return jwt.encode(token, private_key, algorithm=algorithm)

# [END iot_http_jwt]

@retry.Retry(
    predicate=retry.if_exception_type(AssertionError), deadline=_BACKOFF_DURATION
)
# [START iot_http_publish]
def publish_message(
    message
):
    headers = {
        "authorization": "Bearer {}".format(jwt_token),
        "content-type": "application/json",
        "cache-control": "no-cache",
    }

    # Publish to the events or state topic based on the flag.
    url_suffix = "publishEvent" if message_type == "event" else "setState"

    publish_url = ("{}/projects/{}/locations/{}/registries/{}/devices/{}:{}").format(
        base_url, project_id, cloud_region, registry_id, device_id, url_suffix
    )

    body = None
    msg_bytes = base64.urlsafe_b64encode(message.encode("utf-8"))
    if message_type == "event":
        body = {"binary_data": msg_bytes.decode("ascii")}
    else:
        body = {"state": {"binary_data": msg_bytes.decode("ascii")}}

    resp = requests.post(publish_url, data=json.dumps(body), headers=headers)

    if resp.status_code != 200:
        print("Response came back {}, retrying".format(resp.status_code))
        raise AssertionError("Not OK response: {}".format(resp.status_code))

    return resp
# [END iot_http_publish]

@retry.Retry(
    predicate=retry.if_exception_type(AssertionError), deadline=_BACKOFF_DURATION
)
# [START iot_http_getconfig]
def get_config(
    version,
    message_type,
    base_url,
    project_id,
    cloud_region,
    registry_id,
    device_id,
    jwt_token,
):
    headers = {
        "authorization": "Bearer {}".format(jwt_token),
        "content-type": "application/json",
        "cache-control": "no-cache",
    }

    basepath = "{}/projects/{}/locations/{}/registries/{}/devices/{}/"
    template = basepath + "config?local_version={}"
    config_url = template.format(
        base_url, project_id, cloud_region, registry_id, device_id, version
    )

    resp = requests.get(config_url, headers=headers)

    if resp.status_code != 200:
        print("Error getting config: {}, retrying".format(resp.status_code))
        raise AssertionError("Not OK response: {}".format(resp.status_code))

    return resp
# [END iot_http_getconfig]

def parse_command_line_args():
    """Parse command line arguments."""
    
    parser.add_argument(
        "--message",
        type=str,
        help=("Message to send"),
    )

    return parser.parse_args()

# [START iot_http_run]
def main():
    args = parse_command_line_args()
    global jwt_token
    jwt_token = create_jwt(project_id, private_key_file, algorithm)
    jwt_iat = datetime.datetime.now(tz=datetime.timezone.utc)
    jwt_exp_mins = args.jwt_expires_minutes

    print(
        "Latest configuration: {}".format(
            get_config(
                "0",
                message_type,
                base_url,
                project_id,
                cloud_region,
                registry_id,
                device_id,
                jwt_token,
            ).text
        )
    )

    # Publish num_messages mesages to the HTTP bridge once per second.
    seconds_since_issue = (datetime.datetime.now(tz=datetime.timezone.utc) - jwt_iat).seconds
    if seconds_since_issue > 60 * jwt_exp_mins:
        print("Refreshing token after {}s").format(seconds_since_issue)
        jwt_token = create_jwt(
            args.project_id, args.private_key_file, algorithm
        )
        jwt_iat = datetime.datetime.now(tz=datetime.timezone.utc)

    payload = converter(args.message)

    resp = publish_message(
        payload
    )
    print("Finished.")

# [END iot_http_run]

if __name__ == "__main__":
    main()