from django.urls import path

from .api.endpoints.shipment import ShipmentEndpoint

app_name = "shipper"

urlpatterns = [
    path("api/v1/shipments/", ShipmentEndpoint.as_view(), name="create_shipment"),
]
