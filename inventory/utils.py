# inventory/utils.py

def generate_no(model, field, prefix):
    last = model.objects.filter(
        **{f"{field}__startswith": prefix}
    ).order_by(f"-{field}").first()
    
    if last:
        last_number = int(getattr(last, field)[-4:])
        return f"{prefix}{last_number + 1:04d}"
    return f"{prefix}0001"