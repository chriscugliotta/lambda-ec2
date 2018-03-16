#!/bin/bash

# System constants
export ec2_dir="/root"
export ec2_log="$ec2_dir/ec2.log"
export ec2_timeout="8h"
export git_user="<git_user>"
export git_pass="<git_pass>"

# App constants
export app_url="https://$git_user:$git_pass@github.com/$git_user/lambda-ec2.git"
export app_dir="$ec2_dir/lambda-ec2"
export app_requirements="$app_dir/requirements.txt"
export app_in_zip="$app_dir/app/input.zip"
export app_out_zip="$app_dir/app/output.zip"
export app_main="$app_dir/app/main.py"
export app_log="$app_dir/app/log.log"

# S3 constants
export job_id=$(basename "<s3_in_zip>" .zip)
export s3_bucket="<s3_bucket>"
export s3_in_zip="<s3_in_zip>"
export s3_out_zip="app_runner/output/${job_id}.zip"
export s3_ec2_log="app_runner/output/${job_id}_ec2.log"
export s3_app_log="app_runner/output/${job_id}_app.log"

# Logging
mkdir -p "$ec2_dir"
rm -f $ec2_log
exec > >(tee -a $ec2_log) 2>&1
echo "BEGIN at $(date "+%F %T %Z")"



# Installs git, then fetches app code.
function get_app() {
    
    echo "Installing git..."
    yum install -y -q git

    echo "Cloning repository..."
    rm -rf "$app_dir"
    git clone $app_url "$app_dir"
}



# Creates the app's virtualenv instance, and installs libraries via pip.
function create_venv() {

    echo "Installing Python..."
    yum install -y -q python36

    echo "Creating app's virtualenv instance..."
    rm -rf "$app_dir/venv"
    virtualenv --python=python3.6 "$app_dir/venv"

    echo "Activating virtualenv instance..."
    . "$app_dir/venv/bin/activate"

    echo "Installing Python libraries via pip..."
    pip install -r "$app_requirements"

    echo "Printing list of installed Python libraries..."
    pip freeze
}



# Downloads input, runs app, uploads output, cleans up input.
function run_app() {

    echo "Downloading input data from S3..."
    mkdir -p $( dirname "$app_in_zip" )
    aws s3api get-object \
        --bucket "$s3_bucket" \
        --key "$s3_in_zip" \
        "$app_in_zip"

    echo "Running app..."
    python "$app_main"

    echo "Uploading output data to S3..."
    touch "$app_out_zip"
    aws s3api put-object \
        --bucket "$s3_bucket" \
        --key "$s3_out_zip" \
        --body "$app_out_zip"

    # echo "Deleting input data from S3..."
    # aws s3api delete-object \
    #     --bucket "$s3_bucket" \
    #     --key "$s3_in_zip"
}



# This is the primary work load.
function main() {
    get_app
    create_venv
    run_app
}



# Uploads logs to S3.
function upload_logs() {

    # echo "Uploading ec2_log to S3..."
    aws s3api put-object \
        --bucket "$s3_bucket" \
        --key "$s3_ec2_log" \
        --body "$ec2_log"

    echo "Uploading app_log to S3..."
    aws s3api put-object \
        --bucket "$s3_bucket" \
        --key "$s3_app_log" \
        --body "$app_log"
}



# Export functions, so they are exposed to child process
export -f get_app
export -f create_venv
export -f run_app
export -f main



# Entry point to main method.
# The main method is called as a child process, with a timeout condition.
# If it takes too long, the child process is interrupted and killed.
timeout $ec2_timeout bash -ec "main"
exit_status=$?
echo "END at $(date "+%F %T %Z") with exit_status=$exit_status"
upload_logs
shutdown -h now