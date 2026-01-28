import boto3

from app.core.settings import get_settings

# Use a global session and settings
settings = get_settings()
session = boto3.session.Session()
iot_client = session.client("iot", region_name=settings.AWS_REGION)


async def provision_device(device_id: str, policy_name: str) -> dict:
    """
    Provisions a new device in AWS IoT Core.
    1. Creates a new certificate.
    2. Creates a new "Thing" (the device record).
    3. Attaches the certificate to the Thing.
    4. Attaches the operational policy to the certificate.
    """
    print(f"Provisioning device: {device_id} with policy {policy_name}")

    # 1. Create Certificate
    cert_response = iot_client.create_keys_and_certificate(setAsActive=True)
    certificate_pem = cert_response["certificatePem"]
    certificate_arn = cert_response["certificateArn"]
    certificate_id = cert_response["certificateId"]
    private_key = cert_response["keyPair"]["PrivateKey"]

    print(f"Created certificate: {certificate_id}")

    # 2. Create Thing
    try:
        thing_response = iot_client.create_thing(thingName=device_id)
        thing_name = thing_response["thingName"]
        thing_arn = thing_response["thingArn"]
        print(f"Created thing: {thing_name}")
    except iot_client.exceptions.ResourceAlreadyExistsException:
        # If Thing already exists, just get its details
        print(f"Thing {device_id} already exists. Re-using.")
        thing_response = iot_client.describe_thing(thingName=device_id)
        thing_name = thing_response["thingName"]
        thing_arn = thing_response["thingArn"]

    # 3. Attach Certificate to Thing
    iot_client.attach_thing_principal(thingName=thing_name, principal=certificate_arn)
    print(f"Attached certificate {certificate_id} to {thing_name}")

    # 4. Attach Policy to Certificate
    iot_client.attach_policy(policyName=policy_name, target=certificate_arn)
    print(f"Attached policy {policy_name} to {certificate_id}")

    return {
        "certificatePem": certificate_pem,
        "privateKey": private_key,
        "certificateId": certificate_id,
        "thingName": thing_name,
        "thingArn": thing_arn,
    }


async def list_provisioned_devices() -> list[dict]:
    """
    Lists all Things (devices) registered in AWS IoT Core.
    """
    things = []
    paginator = iot_client.get_paginator("list_things")
    for page in paginator.paginate():
        for thing in page["things"]:
            things.append(
                {
                    "thing_name": thing["thingName"],
                    "thing_arn": thing["thingArn"],
                    "attributes": thing.get("attributes", {}),
                }
            )
    return things


async def revoke_device_certificate(certificate_id: str) -> None:
    """
    Revokes a device's certificate by setting its status to REVOKED.
    The ALB's mTLS listener must have revocation checking enabled for this to work.
    """
    print(f"Revoking certificate: {certificate_id}")
    iot_client.update_certificate(certificateId=certificate_id, newStatus="REVOKED")
    # Note: You must also detach the principal from the thing
    # and detach policies if you want a full cleanup.
    # For now, REVOKED is enough to block access.

    principals_response = iot_client.list_thing_principals(
        thingName=iot_client.describe_certificate(certificateId=certificate_id)[
            "certificateDescription"
        ]["certificateArn"].split("/")[-1]  # This is a bit of a hack to get the thing name
    )

    # Detach from all things
    for principal_arn in principals_response["principals"]:
        thing_name = iot_client.list_principal_things(principal=principal_arn)["things"][0]
        iot_client.detach_thing_principal(thingName=thing_name, principal=principal_arn)
        print(f"Detached {certificate_id} from {thing_name}")

    return None
