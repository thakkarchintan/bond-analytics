from firebase_config import firebase_config


# ── Instrument metadata ────────────────────────────────────────────────────────

def get_instrument_metadata() -> dict:
    """Return {instrument_name: {country, asset_class, maturity, notes}} from Firestore."""
    db = firebase_config()
    doc = db.collection("app_config").document("instrument_metadata").get()
    return doc.to_dict() or {} if doc.exists else {}


def save_instrument_metadata(meta_dict: dict) -> None:
    """Overwrite the instrument metadata document in Firestore."""
    db = firebase_config()
    db.collection("app_config").document("instrument_metadata").set(meta_dict)


# ── Formula CRUD ───────────────────────────────────────────────────────────────

def get_formula_list(user_email: str) -> list:
    db = firebase_config()
    doc = db.collection("formulas").document(user_email).get()
    if doc.exists:
        return doc.to_dict().get("formula_list", [])
    return []


def add_formula(user_email: str, formula_text: str) -> None:
    db = firebase_config()
    doc_ref = db.collection("formulas").document(user_email)
    doc = doc_ref.get()
    if doc.exists:
        current_list = doc.to_dict().get("formula_list", [])
        if formula_text not in current_list:
            current_list.append(formula_text)
            doc_ref.set({"formula_list": current_list}, merge=True)
    else:
        doc_ref.set({"formula_list": [formula_text]})


def delete_formula(user_email: str, formula_text: str) -> None:
    db = firebase_config()
    doc_ref = db.collection("formulas").document(user_email)
    doc = doc_ref.get()
    if doc.exists:
        current_list = doc.to_dict().get("formula_list", [])
        if formula_text in current_list:
            current_list.remove(formula_text)
        doc_ref.set({"formula_list": current_list}, merge=True)
