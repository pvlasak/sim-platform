data "aws_availability_zones" "azs" {}

output "azs" {
    value = data.aws_availability_zones.azs.names
}


resource "aws_iam_policy" "cluster_s3" {
  name_prefix = "sim-cluster-s3-"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject"]
        Resource = "arn:aws:s3:::${var.s3_bucket_name}/models/*/revisions/*/*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:AbortMultipartUpload"
        ]
        Resource = "arn:aws:s3:::${var.s3_bucket_name}/results/*"
      },
      {
        Effect   = "Allow"
        Action   = ["s3:ListBucket"]
        Resource = "arn:aws:s3:::${var.s3_bucket_name}"
        Condition = {
          StringLike = {
            "s3:prefix" = [
              "models/*/revisions/*",
              "results/*"
            ]
          }
        }
      }
    ]
  })
}

module "hpc-vpc" {
  source = "terraform-aws-modules/vpc/aws"
  version = "6.6.1"

  name = "hpc-vpc"
  cidr = var.vpc_cidr_block

  azs = data.aws_availability_zones.azs.names
  private_subnets = var.private_subnets
  public_subnets  = var.public_subnets

  enable_nat_gateway = true
  single_nat_gateway = true
  enable_dns_hostnames = true
  enable_dns_support = true

}

module "pcluster" {
  source  = "aws-tf/parallelcluster/aws"
  version = "1.2.0"

  region = var.region
  api_stack_name = var.api_stack_name
  api_version = var.api_version
  deploy_pcluster_api = false
  
  config_path = "${path.module}/config/clusters.yaml"
  template_vars = merge(local.config_vars, {
        s3_policy_arn = aws_iam_policy.cluster_s3.arn
        cluster_config_path = "${path.module}/config/cluster_config.yaml"
        })
}

output "clusters" {
    value = module.pcluster.clusters
}