from django.urls import path

from sauna_data import views

urlpatterns = [
    path("", views.physical_unit_list, name="physical_unit_list"),
    path("units/", views.physical_unit_list, name="physical_unit_list_alt"),
    path("units/<int:unit_id>/", views.physical_unit_detail, name="physical_unit_detail"),
    path(
        "products/<int:product_id>/support/<str:kind>/<int:owner_id>/<str:slot>/",
        views.qc_support_file,
        name="qc_support_file",
    ),
    path("units/<int:unit_id>/qc-form/", views.qc_form_file, name="qc_form_file"),
    path("products/", views.product_list, name="product_list"),
    path("power-boxes/", views.catalog_section, {"section": "power_boxes"}, name="power_box_list"),
    path(
        "control-panels/",
        views.catalog_section,
        {"section": "control_panels"},
        name="control_panel_list",
    ),
    path(
        "firmware-instructions/",
        views.catalog_section,
        {"section": "firmware_instructions"},
        name="firmware_instruction_list",
    ),
    path(
        "products/files/<str:kind>/<int:owner_id>/<str:slot>/",
        views.catalog_support_file,
        name="catalog_file",
    ),
    path("products/<int:product_id>/", views.product_detail, name="product_detail"),
    path("customer-service/", views.customer_service_list, name="customer_service_list"),
    path(
        "customer-service/<int:unit_id>/",
        views.customer_service_detail,
        name="customer_service_detail",
    ),
]
