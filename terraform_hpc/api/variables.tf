variable region {
    description = "The region the ParallelCluster API is deployed in."
    type = string
    default = "eu-central-1"
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