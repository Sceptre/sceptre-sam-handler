# -*- coding: utf-8 -*-
from sceptre.template_handlers import TemplateHandler


class CustomTemplateHandler(TemplateHandler):
    """
    The following instance attributes are inherited from the parent class TemplateHandler.

    Parameters
    ----------
    name: str
        The name of the template. Corresponds to the name of the Stack this template belongs to.
    handler_config: dict
        Configuration of the template handler. All properties except for `type` are available.
    sceptre_user_data: dict
        Sceptre user data defined in the Stack config
    connection_manager: sceptre.connection_manager.ConnectionManager
        Connection manager that can be used to call AWS APIs
    stack_group_config: dict
        Sceptre parameters defined in the Stack group config
    """

    def __init__(self, *args, **kwargs):
        super(CustomTemplateHandler, self).__init__(*args, **kwargs)

    def schema(self):
        """
        Return a JSON schema of the properties that this template handler requires.
        For help filling this, see https://github.com/Julian/jsonschema
        """
        return {
            "type": "object",
            "properties": {},
            "required": []
        }

    def handle(self):
        """
        `handle` should return a CloudFormation template string or bytes. If the return
        value is a byte array, UTF-8 encoding is assumed.

        To use instance attribute self.<attribute_name>. See the class-level docs for a
        list of attributes that are inherited.

        Returns
        -------
        str|bytes
            CloudFormation template
        """
        return ""
