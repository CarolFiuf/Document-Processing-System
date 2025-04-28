variable "resource_group_name" {
  description = "Resource group name"
  type        = string
  default     = "aks-resource-group"
}

variable "location" {
  description = "AZ Region for resources"
  type        = string
  default     = "East US"
}

variable "project_name" {
  description = "Project name to be used as prefix for all resources"
  type        = string
  default     = "traffic-monitoring-system"
}

variable "default_node_pool_name" {
  description = "Name"
  type        = string
  default     = "default"
}

variable "default_node_count" {
  description = "Initial node count"
  type        = number
  default     = 2
}

variable "default_vm_size" {
  description = "VM size"
  type        = string
  default     = "Standard_DS2_v2"
}

variable "enable_auto_scaling" {
  description = "Enable auto scaling for the default node pool"
  type        = bool
  default     = true
}

variable "os_disk_size" {
  description = "OS disk size in GB for nodes"
  type        = number
  default     = 30
}

variable "min_node_count" {
  description = "Minimum node count"
  type        = number
  default     = 2
}

variable "max_node_count" {
  description = "Maximum node count"
  type        = number
  default     = 4
}