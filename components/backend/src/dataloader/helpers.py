def clean_document(document, keys=None):
    cleaned_document = document.copy()
    cleaned_document.pop("_id", None)
    cleaned_document.pop("debate_id", None)
    if not keys:
        return cleaned_document
    for key in keys:
        cleaned_document.pop(key, None)
    return cleaned_document
