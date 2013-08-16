import inflection

def from_foreign_model(tinymodel, foreign_model):
    """
    Translates field values from a foreign model to a TinyModel.
    Assumes that field names of the foreign model match the field names of the TinyModel *exactly*

    :param object foreign_model: The object we want to translate from (e.g. django model, bridge library model, etc)

    :rtype dict: A dict of the attributes to set.

    """
    attrs_to_set = {}
    if foreign_model is None:
        return attrs_to_set

    for field_def in tinymodel.FIELD_DEFS:
        is_id_value = False
        try:
            foreign_value = getattr(foreign_model, field_def.title)
        except AttributeError:
            try:
                foreign_value = getattr(foreign_model, field_def.title + "_id")
                is_id_value = True
            except AttributeError:
                try:
                    foreign_value = getattr(foreign_model, inflection.singularize(field_def.title) + "_ids")
                    is_id_value = True
                except AttributeError:
                    continue
        if field_def.relationship == 'has_many':
            if is_id_value:
                attrs_to_set[inflection.singularize(field_def.title) + "_ids"] = foreign_value
            else:
                child_class = None
                # use first usable allowed_type
                for allowed_type in field_def.allowed_types:
                    child_class = next(iter(allowed_type), None)
                    if child_class not in tinymodel.SUPPORTED_BUILTINS:
                        break
                try:
                    # special case for django
                    if hasattr(foreign_value, "all"):
                        foreign_value = foreign_value.all()
                    # call from_foreign_model recursively
                    attrs_to_set[field_def.title] = [child_class(from_foreign_model=val) for val in foreign_value]
                except TypeError:
                    pass
        elif field_def.relationship == 'has_one':
            if is_id_value:
                attrs_to_set[field_def.title + "_id"] = foreign_value
            else:
                # use first usable allowed_type
                child_class = next((t for t in field_def.allowed_types if t not in tinymodel.SUPPORTED_BUILTINS), None)
                # call from_foreign_model recursively
                attrs_to_set[field_def.title] = child_class(from_foreign_model=foreign_value)
        else:
            attrs_to_set[field_def.title] = foreign_value

    return attrs_to_set
