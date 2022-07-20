# Driftctl cross account - cross region
***
Driftctl is a utility to detect drifts for the resources managed by Terraform as IaC.

## Table of contents
***
* [Pre-requisites](#pre-requisites)
    * [Pre-requisite Steps](#pre-requisites-steps)
* [Driftctl](#driftctl)
  * [Setup](#setup)
  * [Initialize](#initialize-and-apply-terraform-config-and-run-driftctl-to-detect-drifts)
  * [Driftignore (optional)](#add-existing-infrastructure-on-aws-account-to-driftignore-optional)
    * [Generate driftignore](#driftignore-generation-steps)
    * [Re-check driftctl scan](#re-check-driftctl-scan-results)
  * [Introduce drift](#introducing-drift)
  * [Detect drift](#detect-drifts)
* [Cleanup](#cleanup)
* [Limitations](#limitations)
## Pre-requisites
* 2 AWS Account
  * Account A
  * Account B
* Unix shell/Git-bash
  * bash
  * sh 
* Python >= 3.8
* AWS CLI >= 2.2.43
* [jq](https://stedolan.github.io/jq/download/) >= 1.6  
* [terraform](https://www.terraform.io/downloads) >= 1.0
* User configured on both AWS Account with `ReadOnlyAccess`, `AmazonEC2FullAccess` and `AmazonS3FullAccess` policies, following details provided [here](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_users_create.html).
* User security credentials, i.e. `AWS ACCESS KEY ID` and `AWS SECRET ACCESS KEY` for both the accounts, following details provided [here](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html#Using_CreateAccessKey).
> for the shell being used, please ensure interactive_comments is enabled via setopt to allow comments to be ignored for interactive shell

## Pre-requisites steps
* Configure AWS cli profile for user on `Account A`, replacing AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY with user security credential from this account.
    ```shell
    export ACCOUNT_A_ACCESS_KEY_ID=<AWS_ACCESS_KEY_ID>
    export ACCOUNT_A_SECRET_ACCESS_KEY=<AWS_SECRET_ACCESS_KEY>
    
    # Configure profile for Account A, us-east-1 region
    aws configure set aws_access_key_id $ACCOUNT_A_ACCESS_KEY_ID --profile driftctl-acc-a-use1
    aws configure set aws_secret_access_key $ACCOUNT_A_SECRET_ACCESS_KEY --profile driftctl-acc-a-use1
    aws configure set region us-east-1 --profile driftctl-acc-a-use1
    
    # Configure profile for Account A, us-west-1 region
    aws configure set aws_access_key_id $ACCOUNT_A_ACCESS_KEY_ID --profile driftctl-acc-a-usw1
    aws configure set aws_secret_access_key $ACCOUNT_A_SECRET_ACCESS_KEY --profile driftctl-acc-a-usw1
    aws configure set region us-west-1 --profile driftctl-acc-a-usw1
    ```
* Similarly Configure AWS cli profile for user on `Account B`, replacing AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY with user security credential from this account.
    ```shell
    export ACCOUNT_B_ACCESS_KEY_ID=<AWS_ACCESS_KEY_ID>
    export ACCOUNT_B_SECRET_ACCESS_KEY=<AWS_SECRET_ACCESS_KEY>
    
    # Configure profile for Account B, eu-west-1 region
    aws configure set aws_access_key_id $ACCOUNT_B_ACCESS_KEY_ID --profile driftctl-acc-b-euw1
    aws configure set aws_secret_access_key $ACCOUNT_B_SECRET_ACCESS_KEY --profile driftctl-acc-b-euw1
    aws configure set region eu-west-1 --profile driftctl-acc-b-euw1
    
    # Configure profile for Account B, us-west-2 region
    aws configure set aws_access_key_id $ACCOUNT_B_ACCESS_KEY_ID --profile driftctl-acc-b-usw2
    aws configure set aws_secret_access_key $ACCOUNT_B_SECRET_ACCESS_KEY --profile driftctl-acc-b-usw2
    aws configure set region us-west-2 --profile driftctl-acc-b-usw2
    ```

## Driftctl
### Setup
- Install latest version of Driftctl following steps mentioned [here](https://docs.driftctl.com/installation/) and check if the installation is successful using below command.
  ```shell
  driftctl -h
  ```
- Clone this git repository, using below command.
  ```shell
  git clone https://github.com/aws-samples/driftctl-cross-account-cross-region.git && cd driftctl-cross-account-cross-region
  ```
  > As part of this repository, terraform module to create an Amazon EC2 instance (instance type : t2.micro) in default Amazon VPC (i.e. `terraform-aws-ec2`) is located under branch `terraform-module`. 
  Using this module, terraform configuration located under sub-folders of folder named terraform will create ec2 instance in default VPC in `us-east-1` and `us-west-1` AWS regions of `Account A`, and `eu-west-1` and `us-west-1` AWS Regions of `Account B`.
  > For AWS resources supported by driftctl, please refer [this](https://docs.driftctl.com/next/providers/aws/resources) page.
- Setup Python venv, execute below commands to set it up.
  ```shell
  python3 -m venv .env
  source .env/bin/activate
  pip install -r requirements.txt
  ```
### Initialize and apply terraform config and run driftctl to detect drifts
- Run below commands to initialize terraform configuration and apply the configuration in respective account and region.
  ```shell
  terraform -chdir=terraform/account-a/us-east-1 init && terraform -chdir=terraform/account-a/us-east-1 apply --auto-approve
  terraform -chdir=terraform/account-a/us-west-1 init && terraform -chdir=terraform/account-a/us-west-1 apply --auto-approve
  terraform -chdir=terraform/account-b/eu-west-1 init && terraform -chdir=terraform/account-b/eu-west-1 apply --auto-approve
  terraform -chdir=terraform/account-b/us-west-2 init && terraform -chdir=terraform/account-b/us-west-2 apply --auto-approve
  ```
- Run below commands to run driftctl scan for terraform configurations state file located inside their respective account and region folders. 
  Each line of the command will run drift thrice, to show detected drift on console and generate driftctl scan output in json and html format for further steps.
  >Note : If ThrottlingException: Rate exceeded is encountered on execution of the below commands, please consider increasing service quota for `Account A` and `Account B`.
  ```shell
  # DriftCTL Scan for `Account A` resources in region `us-east-1` region along with Global AWS resource like IAM, S3, R53 and others.
   unset AWS_DEFAULT_REGION && unset AWS_PROFILE;\
    AWS_PROFILE=driftctl-acc-a-use1 driftctl scan --from tfstate://terraform/account-a/us-east-1/terraform.tfstate; \
    # Generate Driftctl Scan output in machine readable JSON format.
    AWS_PROFILE=driftctl-acc-a-use1 driftctl scan --from tfstate://terraform/account-a/us-east-1/terraform.tfstate --output json://terraform/account-a/us-east-1/driftctl-result.json; \
    # Generate Driftctl Scan output in human readable HTML format.
    AWS_PROFILE=driftctl-acc-a-use1 driftctl scan --from tfstate://terraform/account-a/us-east-1/terraform.tfstate --output html://terraform/account-a/us-east-1/driftctl-result.html
  ```
  ```shell
  # DriftCTL Scan for `Account A` resources in region `us-west-1` region along with Global AWS resource like IAM, S3, R53 and others.
  unset AWS_DEFAULT_REGION && unset AWS_PROFILE;\
    AWS_PROFILE=driftctl-acc-a-usw1  driftctl scan --from tfstate://terraform/account-a/us-west-1/terraform.tfstate ; \
    # Generate Driftctl Scan output in machine readable JSON format.
    AWS_PROFILE=driftctl-acc-a-usw1 driftctl scan --from tfstate://terraform/account-a/us-west-1/terraform.tfstate --output json://terraform/account-a/us-west-1/driftctl-result.json; \
    # Generate Driftctl Scan output in human readable HTML format.
    AWS_PROFILE=driftctl-acc-a-usw1 driftctl scan --from tfstate://terraform/account-a/us-west-1/terraform.tfstate --output html://terraform/account-a/us-west-1/driftctl-result.html
  ```
  ```shell
  # DriftCTL Scan for `Account B` resources in region `eu-west-1` region along with Global AWS resource like IAM, S3, R53 and others.
  unset AWS_DEFAULT_REGION && unset AWS_PROFILE;\
    AWS_PROFILE=driftctl-acc-b-euw1 driftctl scan --from tfstate://terraform/account-b/eu-west-1/terraform.tfstate ; \
    # Generate Driftctl Scan output in machine readable JSON format.
    AWS_PROFILE=driftctl-acc-b-euw1 driftctl scan --from tfstate://terraform/account-b/eu-west-1/terraform.tfstate --output json://terraform/account-b/eu-west-1/driftctl-result.json ; \
    # Generate Driftctl Scan output in human readable HTML format.
    AWS_PROFILE=driftctl-acc-b-euw1 driftctl scan --from tfstate://terraform/account-b/eu-west-1/terraform.tfstate --output html://terraform/account-b/eu-west-1/driftctl-result.html
  ```
  ```shell
  # DriftCTL Scan for `Account B` resources in region `us-west-2` region along with Global AWS resource like IAM, S3, R53 and others.
   unset AWS_DEFAULT_REGION && unset AWS_PROFILE;\
    AWS_PROFILE=driftctl-acc-b-usw2 driftctl scan --from tfstate://terraform/account-b/us-west-2/terraform.tfstate ; \
    # Generate Driftctl Scan output in machine readable JSON format.
    AWS_PROFILE=driftctl-acc-b-usw2 driftctl scan --from tfstate://terraform/account-b/us-west-2/terraform.tfstate --output json://terraform/account-b/us-west-2/driftctl-result.json; \
    # Generate Driftctl Scan output in human readable HTML format.
    AWS_PROFILE=driftctl-acc-b-usw2 driftctl scan --from tfstate://terraform/account-b/us-west-2/terraform.tfstate --output html://terraform/account-b/us-west-2/driftctl-result.html
  ```
- Verify the output from each of 4 driftctl scan command, it should similar to the one mentioned below.
  If there are any resources already present in the account, driftctl scan result will show them as unmanaged, if you wish to ignore these unmanaged resources ( not managed by terraform ), please refer to [this](#add-existing-infrastructure-on-aws-account-to-driftignore-optional) section.
  ```text
  Found 62 resource(s)
   - 3% coverage
   - 2 resource(s) managed by terraform
   - 60 resource(s) not managed by Terraform
   - 0 resource(s) found in a Terraform state but missing on the cloud provider
  Scan duration: 5s
  ```
  Alternatively you can traverse to folders holding terraform configuration (e.g. terraform/account-a/us-east-1) and validate the drift results from driftctl-result.html file.
  If you wish to merge driftctl scan output from multiple folder, please use the python script with this repository, this python script by default searches for all driftctl-result.json file(s) from current location and generates a tabular output. 
  ```shell
  python3 driftctl_result.py
  ```
  > Python script `driftctl_result.py`, by default scans all subdirectories and looks for driftctl-result.json file and combines details from these files and produces a combined summary and detailed output in tabular format. 
  > In addition, the script executes `terraform output` command at the location where driftctl-result.json is found, and extracts `resource_region` and `resource_account_id` output values to populate region and account id details in detailed output.
  > Use python3 `driftctl_result.py -h ` to view all available options

### Add existing infrastructure on AWS Account to .driftignore (Optional)
Many users/enterprises do not have the goal of reaching a 100% IAC coverage with their infrastructure. And for them, driftctl can be annoying to continuously deliver drift notifications on resources they don't care. For this use case, there's a solution.

You can start using driftctl with a clean state, by ignoring all the current resources that are not yet under control. driftctl provides a command to automatically generate a .driftignore file from a previous scan given the type of resources you want to exclude (e.g. unmanaged, missing or changed resources).

#### driftignore generation steps
1. Run below commands to generate driftignore for each terraform configuration located under terraform folder of the checked out repository. With this all supported AWS resources that are currently not managed with terraform configuration will be ignored from further scans. 
  ```shell
  driftctl gen-driftignore -i terraform/account-a/us-east-1/driftctl-result.json -o terraform/account-a/us-east-1/.driftignore
  driftctl gen-driftignore -i terraform/account-a/us-west-1/driftctl-result.json -o terraform/account-a/us-west-1/.driftignore
  driftctl gen-driftignore -i terraform/account-b/eu-west-1/driftctl-result.json -o terraform/account-b/eu-west-1/.driftignore
  driftctl gen-driftignore -i terraform/account-b/us-west-2/driftctl-result.json -o terraform/account-b/us-west-2/.driftignore
  ```
#### Re-check driftctl scan results
Lets check if driftctl scan results coverage is 100% with driftignore shows that all resources are managed by terraform now.

Below command is to re-check drift results for `Account A` in `us-east-1` region, use similar account to validate coverage for remaining account(s) and region(s).
```shell
  unset AWS_DEFAULT_REGION && unset AWS_PROFILE && \
    AWS_PROFILE=driftctl-acc-a-use1 driftctl scan --from tfstate://terraform/account-a/us-east-1/terraform.tfstate --driftignore terraform/account-a/us-east-1/.driftignore;
```
Output from above command should be similar to below.
  ```text
  Scanned states (1)
  Found 2 resource(s)
   - 100% coverage
  Congrats! Your infrastructure is fully in sync.
  Scan duration: 6s
  ```

### Introducing drift
Now let's add some drift by manually adding tags, stopping instance and changing security groups for the instances. You can introduce the drift manually using console, but we will be introducing drift using AWS CLI.  
1. Add Tags to the instance running in `Account A` within `us-east-1` region.
  ```shell
  instance_id=$(terraform -chdir=terraform/account-a/us-east-1 output -json | jq -r '.instance_id|.value')
  aws ec2 create-tags --resources $instance_id --tags Key=DummyTag,Value=DummyValue --profile driftctl-acc-a-use1
  ```
2. Stop the instance running in `Account A` within `us-west-1` region.
  ```shell
  instance_id=$(terraform -chdir=terraform/account-a/us-west-1 output -json | jq -r '.instance_id|.value')
  aws ec2 stop-instances --instance-ids $instance_id --profile driftctl-acc-a-usw1
  ```
3. Added security group to instance running in `Account B` within `eu-west-1` region.
  ```shell
  vpc_id=$(terraform -chdir=terraform/account-b/eu-west-1 output -json | jq -r '.vpc_id|.value')
  instance_id=$(terraform -chdir=terraform/account-b/eu-west-1 output -json | jq -r '.instance_id|.value')
  security_group_id=$(aws ec2 create-security-group --description "Security group created for Driftctl Demo" --group-name "driftctl-demo-sg" --vpc-id $vpc_id --output json --profile driftctl-acc-b-euw1 | jq -r '.GroupId')
  aws ec2 modify-instance-attribute --instance-id $instance_id --groups $security_group_id --profile driftctl-acc-b-euw1
  ```
4. Terminate the running instance in `Account B` within `us-west-2` region.
  ```shell
  instance_id=$(terraform -chdir=terraform/account-b/us-west-2 output -json | jq -r '.instance_id|.value')
  aws ec2 terminate-instances --instance-ids $instance_id --profile driftctl-acc-b-usw2
  ```
    
### Detect drifts
Following similar steps used during initialization lets run driftcl scan to detect the drifts.
- For Account A, us-east-1 region, we need to detect changes in tags we need to use deep mode while performing driftctl scan.
  ```shell
  # DriftCTL Scan for `Account A` resources in region `us-east-1` region along with Global AWS resource like IAM, S3, R53 and others.
  DRIFTIGNOREFLAG="";\
  if [ -e "./terraform/account-a/us-east-1/.driftignore" ]; then DRIFTIGNOREFLAG="--driftignore ./terraform/account-a/us-east-1/.driftignore";fi; \
  unset AWS_DEFAULT_REGION && unset AWS_PROFILE && \
    AWS_PROFILE=driftctl-acc-a-use1 driftctl scan --from tfstate://terraform/account-a/us-east-1/terraform.tfstate $DRIFTIGNOREFLAG --deep; \
    # Generate Driftctl Scan output in machine readable JSON format.
    AWS_PROFILE=driftctl-acc-a-use1 driftctl scan --from tfstate://terraform/account-a/us-east-1/terraform.tfstate --output json://terraform/account-a/us-east-1/driftctl-result.json $DRIFTIGNOREFLAG --deep; \
    # Generate Driftctl Scan output in human readable HTML format.
    AWS_PROFILE=driftctl-acc-a-use1 driftctl scan --from tfstate://terraform/account-a/us-east-1/terraform.tfstate --output html://terraform/account-a/us-east-1/driftctl-result.html $DRIFTIGNOREFLAG --deep
  ```
- For detecting drift on Account A, us-west-1 region. Run below command.
  ```shell
  DRIFTIGNOREFLAG="";\
  if [ -e "./terraform/account-a/us-west-1/.driftignore" ]; then DRIFTIGNOREFLAG="--driftignore ./terraform/account-a/us-west-1/.driftignore";fi; \
  unset AWS_DEFAULT_REGION && unset AWS_PROFILE && \
    AWS_PROFILE=driftctl-acc-a-usw1 driftctl scan --from tfstate://terraform/account-a/us-west-1/terraform.tfstate $DRIFTIGNOREFLAG --deep; \
    # Generate Driftctl Scan output in machine readable JSON format.
    AWS_PROFILE=driftctl-acc-a-usw1 driftctl scan --from tfstate://terraform/account-a/us-west-1/terraform.tfstate --output json://terraform/account-a/us-west-1/driftctl-result.json --deep $DRIFTIGNOREFLAG; \
    # Generate Driftctl Scan output in human readable HTML format.
    AWS_PROFILE=driftctl-acc-a-usw1 driftctl scan --from tfstate://terraform/account-a/us-west-1/terraform.tfstate --output html://terraform/account-a/us-west-1/driftctl-result.html --deep $DRIFTIGNOREFLAG
  ```
- For detecting drift in Account B, eu-west-1 region, Run below command. Driftctl scan result will show security group created as a unmanaged resource.
  ```shell
  DRIFTIGNOREFLAG=""; \
  if [ -e "./terraform/account-b/eu-west-1/.driftignore" ]; then DRIFTIGNOREFLAG="--driftignore ./terraform/account-b/eu-west-1/.driftignore";fi; \
  # DriftCTL Scan for `Account B` resources in region `eu-west-1` region along with Global AWS resource like IAM, S3, R53 and others.
  unset AWS_DEFAULT_REGION && unset AWS_PROFILE && \
    AWS_PROFILE=driftctl-acc-b-euw1 driftctl scan --from tfstate://terraform/account-b/eu-west-1/terraform.tfstate $DRIFTIGNOREFLAG; \
    # Generate Driftctl Scan output in machine readable JSON format.
    AWS_PROFILE=driftctl-acc-b-euw1 driftctl scan --from tfstate://terraform/account-b/eu-west-1/terraform.tfstate --output json://terraform/account-b/eu-west-1/driftctl-result.json --deep $DRIFTIGNOREFLAG; \
    # Generate Driftctl Scan output in human readable HTML format.
    AWS_PROFILE=driftctl-acc-b-euw1 driftctl scan --from tfstate://terraform/account-b/eu-west-1/terraform.tfstate --output html://terraform/account-b/eu-west-1/driftctl-result.html --deep $DRIFTIGNOREFLAG
  ```
- For detecting drift in Account B, us-west-2 region, Run below command, Driftctl scan result will report a missing resource from managed infrastructure.
  ```shell
  DRIFTIGNOREFLAG=""; \
  if [ -e "./terraform/account-b/us-west-2/.driftignore" ]; then DRIFTIGNOREFLAG="--driftignore ./terraform/account-b/us-west-2/.driftignore";fi; \
  unset AWS_DEFAULT_REGION && unset AWS_PROFILE && \
    AWS_PROFILE=driftctl-acc-b-usw2 driftctl scan --from tfstate://terraform/account-b/us-west-2/terraform.tfstate $DRIFTIGNOREFLAG; \
    # Generate Driftctl Scan output in machine readable JSON format.
    AWS_PROFILE=driftctl-acc-b-usw2 driftctl scan --from tfstate://terraform/account-b/us-west-2/terraform.tfstate --output json://terraform/account-b/us-west-2/driftctl-result.json $DRIFTIGNOREFLAG; \
    # Generate Driftctl Scan output in human readable HTML format.
    AWS_PROFILE=driftctl-acc-b-usw2 driftctl scan --from tfstate://terraform/account-b/us-west-2/terraform.tfstate --output html://terraform/account-b/us-west-2/driftctl-result.html $DRIFTIGNOREFLAG;
  ```
- Combine all detected drifts with python script, run below command.
  ```shell
    # For summary.
    python3 driftctl_result.py 
    # For detailed output.
    python3 driftctl_result.py --detailed
  ```
## Cleanup
- Run below commands to destroy AWS resources created by terraform configuration.
  ```shell
  terraform -chdir=terraform/account-a/us-east-1 destroy --auto-approve
  terraform -chdir=terraform/account-a/us-west-1 destroy --auto-approve
  terraform -chdir=terraform/account-b/eu-west-1 destroy --auto-approve
  terraform -chdir=terraform/account-b/us-west-2 destroy --auto-approve
  aws ec2 delete-security-group --group-name "driftctl-demo-sg" --profile driftctl-acc-b-euw1
  pip3 uninstall -r requirements.txt -y
  deactivate
  rm -r .env/
  ```

## Limitations
For known limitation of driftctl please refer [this](https://docs.driftctl.com/0.17.0/limitations/) page.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.
