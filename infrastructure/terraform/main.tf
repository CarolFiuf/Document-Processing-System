terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "=3.117.0"
    }
  }
  # required_version = ">= 1.2.0"
}

provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "traffic_monitoring_system" {
  name     = var.project_name
  location = var.location
}

resource "azurerm_kubernetes_cluster" "aks" {
  name                = "${var.project_name}-aks"
  location            = azurerm_resource_group.traffic_monitoring_system.location
  resource_group_name = azurerm_resource_group.traffic_monitoring_system.name
  dns_prefix          = "${var.project_name}-aks"

  default_node_pool {
    name       = var.default_node_pool_name
    node_count = var.default_node_count
    vm_size    = var.default_vm_size

    # enable_auto_scaling = var.enable_auto_scaling
    min_count = var.min_node_count
    max_count = var.max_node_count
    os_disk_size_gb = var.os_disk_size
  }
  identity {
    type = "SystemAssigned"
  }
}
