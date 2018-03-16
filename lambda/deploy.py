import boto3
import time
import zipfile



def create_stack(template_path, stack_name, cfn):
    """
    Creates a stack, waits until complete, then returns output.
    """

    # Get CFN template
    with open(template_path, 'r') as file:
        template_body = file.read()

    # Create stack
    cfn.create_stack(
        StackName=stack_name,
        TemplateBody=template_body,
        Capabilities=['CAPABILITY_NAMED_IAM']
    )
    print('Creating stack...')

    # Wait
    waiter = cfn.get_waiter('stack_create_complete').wait(
        StackName=stack_name,
        WaiterConfig={ 'Delay': 15, 'MaxAttempts': 20 }
    )
    print('Done!')

    # Convert stack output list into dict
    output_dict = {}
    output_list = cfn.describe_stacks(StackName=stack_name)['Stacks'][0]['Outputs']
    for output in output_list:
        key = output['OutputKey']
        value = output['OutputValue']
        output_dict[key] = value
        print('{0} = {1}'.format(key, value))

    # Return stack output
    return output_dict



def update_lambda_code(bucket_name, function_name, s3, lamb):
    """
    Packages, uploads, and updates Lambda function code.
    """

    # Paths
    zip_local = 'lambda_code.zip'
    zip_remote = 'app_runner/lambda_code.zip'

    # Package
    with zipfile.ZipFile(zip_local, 'w') as zip:
        zip.write('ec2_init.sh', 'ec2_init.sh')
        zip.write('ec2_run.py', 'ec2_run.py')

    # Upload
    s3.upload_file(zip_local, bucket_name, zip_remote)
    print('Uploaded {0}'.format(zip_remote))

    # Update
    lamb.update_function_code(
        FunctionName=function_name,
        S3Bucket=bucket_name,
        S3Key=zip_remote
    )
    print('Updated {0}'.format(function_name))



def run_e2e_test(bucket_name, s3):
    """
    Runs an end-to-end test.
    """

    # Delete output files (in case they already exist, from a previous run)
    s3.delete_objects(
        Bucket=bucket_name,
        Delete={
            'Objects': [
                { 'Key': 'app_runner/input/test.zip' },
                { 'Key': 'app_runner/input/test_ec2.log' },
                { 'Key': 'app_runner/input/test_app.log' }
            ]
        }
    )

    # Simulate input CSV
    with open('test.csv', 'w') as file:
        file.write('employee_id,salary\n')
        file.write('1,30000\n')
        file.write('2,45000\n')
        file.write('3,80000')

    # Add to zip
    with zipfile.ZipFile('test.zip', 'w') as zip:
        zip.write('test.csv', 'test.csv')

    # Upload input zip to S3
    s3.upload_file('test.zip', bucket_name, 'app_runner/input/test.zip')

    # Wait loop
    found_zip = False
    found_log = False
    delay = 15
    max_attempts = 5 * 4
    for _ in range(max_attempts):

        # Query S3
        response = s3.list_objects(Bucket=bucket_name, Prefix='app_runner/output/')

        # Check if output zip has appeared
        if 'Contents' in response:
            for obj in response['Contents']:
                if obj['Size'] > 0:
                    print('Found {0}'.format(obj['Key']))
                    file_name = obj['Key'].split('/')[-1]
                    if file_name == 'test.zip': found_zip = True
                    if file_name == 'test_ec2.log': found_log = True

        # Check if we're done
        if found_zip:
            print('Done!')
            return
        elif found_log:
            raise Exception('Found log, but no zip')
        else:
            print('Waiting...')
            time.sleep(delay)

    # If we've made it this far, we've timed out...
    raise Exception('Timeout reached')



if __name__ == '__main__':
    """
    Main method.
    """

    # Constants
    profile_name = 'personal'
    region_name = 'us-east-1'

    # boto3 clients
    session = boto3.session.Session(profile_name=profile_name, region_name=region_name)
    cfn = session.client('cloudformation')
    lamb = session.client('lambda')
    s3 = session.client('s3')

    # Create stack
    stack_output = create_stack('deploy.yaml', 'demo', cfn)
    bucket_name = stack_output['DemoBucketArn'].split(':')[-1]
    function_name = stack_output['DemoLambdaFunctionArn'].split(':')[-1]

    # Update Lambda code
    update_lambda_code(bucket_name, function_name, s3, lamb)

    # Run end-to-end test
    run_e2e_test(bucket_name, s3)