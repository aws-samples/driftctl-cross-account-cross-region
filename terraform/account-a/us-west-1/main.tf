provider "aws" {
  profile = "driftctl-acc-a-usw1"
  region  = "us-west-1"
}

module "ec2" {
  source = "git::https://github.com/aws-samples/driftctl-cross-account-cross-region//terraform-aws-ec2?ref=terraform-module"
  name   = "driftctl-acc-a-usw1"
}
