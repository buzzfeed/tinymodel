import inflection


class ModelException(Exception):
    pass


class ValidationError(Exception):
    pass


def get_field_def_names(field_def):
    from tinymodel import Field
    if isinstance(field_def, Field):
        field_def = field_def.field_def
    names = [field_def.title]
    if field_def.relationship == 'has_many':
        names.append(inflection.singularize(field_def.title) + '_ids')
    elif field_def.relationship == 'has_one':
        names.append(field_def.title + '_id')
    return names
