terraform {
  required_version = ">= 0.12"
  backend "s3" {
    bucket = "terraform-state-sim-app"
    key    = "sim-app/terraform.tfstate"
    region = "eu-central-1"
  }
}

provider "aws" {
    region = "eu-central-1"
}

variable vpc_cidr_block {
  default = "10.0.0.0/16"
}
variable private_subnets {
  default = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}
variable public_subnets {
  default = ["10.0.10.0/24", "10.0.11.0/24", "10.0.12.0/24"]
}
variable instance_types {
  default = ["t2.large"]
}

data "aws_availability_zones" "azs" {}


module "sim-app-vpc" {
  source = "terraform-aws-modules/vpc/aws"
  version = "6.6.1"

  name = "sim-app-vpc"
  cidr = var.vpc_cidr_block

  azs = data.aws_availability_zones.azs.names
  private_subnets = var.private_subnets
  public_subnets  = var.public_subnets

  enable_nat_gateway = true
  single_nat_gateway = true
  enable_dns_hostnames = true

  tags = {
	"kubernetes.io/cluster/sim-app-cluster" = "shared"
  }
  public_subnet_tags = {
    "kubernetes.io/cluster/sim-app-cluster" = "shared"
    "kubernetes.io/role/elb"                    = "1"
  }
  private_subnet_tags = {
    "kubernetes.io/cluster/sim-app-cluster" = "shared"
    "kubernetes.io/role/internal-elb"           = "1"
  }
}

output "azs" {
    value = data.aws_availability_zones.azs.names
}

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 21.0"

  name               = "sim-app-cluster"
  kubernetes_version = "1.35"
  enable_irsa = true


  addons = {
    coredns                = {}
    eks-pod-identity-agent = {
      before_compute = true
    }
    aws-ebs-csi-driver = {
      service_account_role_arn = module.ebs_csi_driver_irsa.arn
    }
    kube-proxy             = {}
    vpc-cni                = {
      before_compute = true
    }
  }

  endpoint_public_access = true
  enable_cluster_creator_admin_permissions = true

  vpc_id                   =  module.sim-app-vpc.vpc_id
  subnet_ids               =  module.sim-app-vpc.private_subnets

  # EKS Managed Node Group(s)
  eks_managed_node_groups = {
    eks_ng = {
      # Starting on 1.30, AL2023 is the default AMI type for EKS managed node groups
      ami_type       = "AL2023_x86_64_STANDARD"
      instance_types = var.instance_types

      min_size     = 1
      max_size     = 4
      desired_size = 2
    }
  } 


  tags = {
	  environment = "dev"
    application = "sim-app"
  }
}

module "ebs_csi_driver_irsa" {
  source = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts"

  name = "ebs-csi"

  attach_ebs_csi_policy = true

  oidc_providers = {
    this = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["kube-system:ebs-csi-controller-sa"]
    }
  }

  tags = {
	  environment = "dev"
    application = "sim-app"
  }
}

/* IAM Role configured using Terraform module
module "eks_autoscaler_irsa" {
  source = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts"

  name = "AutoscalerRole"
  attach_cluster_autoscaler_policy = true 
  cluster_autoscaler_cluster_names = ["sim-app-cluster"]

  oidc_providers = {
      this = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["kube-system:cluster-autoscaler"]
    }
  }
}*/

resource "aws_iam_policy" "autoscaler-policy" {
  name = "autoscaler-policy"

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "autoscaling:DescribeAutoScalingGroups",
        "autoscaling:DescribeAutoScalingInstances",
        "autoscaling:DescribeLaunchConfigurations",
        "autoscaling:DescribeScalingActivities",
        "ec2:DescribeImages",
        "ec2:DescribeInstanceTypes",
        "ec2:DescribeLaunchTemplateVersions",
        "ec2:GetInstanceTypesFromInstanceRequirements",
        "eks:DescribeNodegroup"
      ],
      "Resource": ["*"]
    },
    {
      "Effect": "Allow",
      "Action": [
        "autoscaling:SetDesiredCapacity",
        "autoscaling:TerminateInstanceInAutoScalingGroup"
      ],
      "Resource": ["*"]
    }
    ]
  })
}

resource "aws_iam_role" "autoscaler-role" {
  name = "autoscaler-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Action    = "sts:AssumeRoleWithWebIdentity"
      Principal = { Federated = module.eks.oidc_provider_arn }
      Condition = {
        StringEquals = {
          "${module.eks.oidc_provider}:sub" = "system:serviceaccount:kube-system:cluster-autoscaler"
          "${module.eks.oidc_provider}:aud" = "sts.amazonaws.com"
        }
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "policy-attachment" {
  role       = aws_iam_role.autoscaler-role.name
  policy_arn = aws_iam_policy.autoscaler-policy.arn
}

output "AutoScalerRoleARN" {
  value = aws_iam_role.autoscaler-role.arn
}
