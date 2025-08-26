terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "=3.0"
    }
  }
  required_version = ">= 1.0"
}

provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "traffic_monitoring_system" {
  name     = "${var.project_name}-rg"
  location = var.location
}

resource "azurerm_kubernetes_cluster" "aks" {
  name                = "${var.project_name}-aks"
  location            = azurerm_resource_group.traffic_monitoring_system.location
  resource_group_name = azurerm_resource_group.traffic_monitoring_system.name
  dns_prefix          = "${var.project_name}-aks"

  default_node_pool {
    name       = var.default_node_pool_name
    node_count = 1
    vm_size    = var.default_vm_size
    auto_scaling_enabled = true
    min_count = 1
    max_count = 3
    os_disk_size_gb = var.os_disk_size
  }
  identity {
    type = "SystemAssigned"
  }
}
