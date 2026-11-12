variable region {
    description = "The region the ParallelCluster API is deployed in."
    type = string
    default = "eu-central-1"
    }

variable "cluster_region" {
    description = "The region the clusters will be deployed in."
    type = string
    default = "eu-central-1"
}

variable s3_bucket_name {
  description = "Bucket containing model packages and simulation results"
  type        = string
}

variable api_stack_name {
    type = string
    description = "The name of the CloudFormation stack used to deploy the ParallelCluster API."
    default = "ParallelCluster"
}

variable "api_version" {
    type = string
    description = "The version of the ParallelCluster API"
}

variable vpc_cidr_block {
    type = string
}

variable private_subnets {
    type = list(string)
}

variable public_subnets {
    type = list(string)
}  
