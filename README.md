# Contents

- [Background](#background)
- [How It Works](#how-it-works)
- [Hosted App Requirements](#hosted-app-requirements)
- [Hosted App Configuration](#hosted-app-configuration)
- [How to Run](#how-to-run)
- [How to Deploy](#how-to-deploy)

# Background

This AWS stack aims to:
- Trigger an arbitrary Python application in response to an S3 upload.
- Automate deployment of the hosted application's latest source code.
- Streamline and automate environment setup.
- Minimize costs by using on-demand EC2 instances.

# How It Works

When using EC2, we are billed by the hour.  Many applications only need to run periodically, e.g. once a week, so it would be wasteful to keep an EC2 online permanently.  Thus, instead, we will create temporary EC2 instances on-demand, and terminate them when finished.

So, the end-to-end process flow is as follows:

- Some external process uploads an input file to S3.
- This triggers a Lambda function, which [launches](https://docs.aws.amazon.com/cli/latest/reference/ec2/run-instances.html) a new EC2 instance, and passes in an [init script](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/user-data.html). The init script actually does more than initialization. It oversees the entire lifespan of the EC2. It does the following:
    - Fetches the application source code from GitHub.
    - Installs Python and any required libraries.
    - Downloads the input file from S3.
    - Runs the application.
    - Uploads the output file to S3.
    - If the steps above produce any error, or if they take too long, we immediately skip ahead to the next step…
    - Uploads logs to S3.
    - Shuts down, causing EC2 to terminate itself.

So, even if an error occurs, a log should *always* get uploaded to S3, and the EC2 should *always* terminate itself.

# Hosted App Requirements

As mentioned above, the EC2 init script is the entity that actually *calls* the application.  In fact, the init script is very flexible.  It can run any Python application that meets the following criteria:

- It is written in Python, and compatible with Python 3.6.
- It is available on GitHub.
- It has a `requirements.txt` file, containing all library dependencies. 
- It has a single entry point, e.g. `main.py`, which requires no command line arguments.
- It always loads all input data from a single zip file, at a predetermined path.
- It always dumps all output data into a single zip file, at a predetermined path.

# Hosted App Configuration

The requirements above are intentionally vague, to allow for flexibility in the hosted app's directory structure.  However, in order to operate, the init script needs more information about the hosted app.  For example, *where* exactly is the requirements file?  Which script is the entry point?  And so on.

These questions are answered via the parameters atop `lambda/ec2_init.sh`:

- `app_url`:  The app's git clone URL, e.g. `https://chriscugliotta:mypassword@github.com/chriscugliotta/lambda-ec2.git`
- `app_requirements`:  Relative path of `requirements.txt`, e.g. `requirements.txt`.
- `app_in_zip`:  Relative path of input data zip, e.g. `data/input.zip`.
- `app_out_zip`:  Relative path of output data zip, e.g. `data/output.zip`.
- `app_main`:  Relative path of entry point script, e.g. `src/main.py`.
- `app_log`:  Relative path of Python log, e.g. `log.log`.
- `ec2_timeout`:  The EC2 will never run longer than this, e.g. `60s`, `15m`, or `8h`.

**Note:**  Above, all file paths are expressed relative to the repository root directory.  For example, if the full path is `path/to/repo/src/main.py`, then the relative path is `src/main.py`.

# How to Run

To run the hosted application, upload an input file to `app_runner/input/{job_id}.zip`.

When finished, three output files will be uploaded to S3:

- Output data at: `app_runner/output/{job_id}.zip`.
- Init script log at: `app_runner/output/{job_id}_ec2.log`.
- Python log at: `app_runner/output/{job_id}_app.log`.

# How to Deploy

- Customize the parameters at the top of `lambda/ec2_init.sh`.
- Run `deploy/deploy.py` from an AWS profile with administrative access.