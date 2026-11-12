terraform {
  required_version = ">= 1.5.7"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "6.59.0"
        }
    aws-parallelcluster = {
        source = "aws-tf/aws-parallelcluster"
        version = "~> 1.0"
        }
    }
}