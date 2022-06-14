provider "aws" {
  profile = "driftctl-acc-a-use1"
  region  = "us-east-1"
}

module "ec2" {
  source = "git::https://github.com/aws-samples/driftctl-cross-account-cross-region//terraform-aws-ec2?ref=terraform-module"
  name   = "driftctl-acc-a-use1"
}
