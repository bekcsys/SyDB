from django import forms

from sauna_data.models import Product, ProductItem


class PhysicalUnitQcForm(forms.ModelForm):
    class Meta:
        model = ProductItem
        fields = ("product", "qc_tester_name", "qc_status", "note")
        labels = {
            "product": "Product",
            "qc_tester_name": "QC tester name",
            "qc_status": "QC status",
            "note": "Note",
        }
        widgets = {
            "qc_tester_name": forms.TextInput(attrs={"aria-label": "QC tester name"}),
            "qc_status": forms.Select(attrs={"aria-label": "QC status"}),
            "note": forms.Textarea(
                attrs={"rows": 4, "aria-label": "Note", "placeholder": "QC note"},
            ),
        }


class ProductNameField(forms.ModelChoiceField):
    def label_from_instance(self, obj: Product) -> str:
        return obj.product_name
