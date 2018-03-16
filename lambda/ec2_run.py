import boto3



def handler(event, context):

    # Extract bucket name and uploaded file from event object
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    print('File uploaded at bucket = {0}, key = {1}'.format(bucket, key))

    # Substitute parameters into EC2 init script
    with open('ec2_init.sh', 'r') as file:
        init_script = file.read()
        init_script = init_script.replace('<s3_bucket>', bucket)
        init_script = init_script.replace('<s3_in_zip>', key)

    # Launch EC2 instance
    instance = boto3.client('ec2').run_instances(
        IamInstanceProfile={'Name': 'demo-instance-profile'},
        ImageId='ami-97785bed',
        InstanceInitiatedShutdownBehavior='terminate',
        InstanceType='t2.micro',
        KeyName='demo-key-pair',
        MinCount=1,
        MaxCount=1,
        SecurityGroups=['demo-security-group'],
        UserData=init_script
    )

    # Display EC2 instance's IP address
    ec2_private_ip = instance['Instances'][0]['PrivateIpAddress']
    print('EC2 launched at {0}'.format(ec2_private_ip))




if __name__ == '__main__':
    """
    This section will NOT get called in a real Lambda environment.  Thus, it can
    be used as an entry point for manual tests, e.g. during PyCharm development.
    """

    # Mock event object
    event = {
        'Records': [{
            's3': {
                'bucket': {
                    'name': 'demo-bucket-426369505564'
                },
                'object': {
                    'key': 'app_runner/input/test.zip'
                }
            }
        }]
    }

    # Call Lambda function
    handler(event, None)
