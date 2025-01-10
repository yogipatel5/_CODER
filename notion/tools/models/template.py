"""
Models for Notion page templates.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ValidationInfo, field_validator

from notion.tools.models.page import BlockContent, PageProperties, ParentType


class TemplateVariable(BaseModel):
    """Variable placeholder in a template."""

    name: str = Field(..., description="Variable name")
    description: str = Field(..., description="Variable description")
    required: bool = Field(True, description="Whether the variable is required")
    default: Optional[Any] = Field(None, description="Default value if not provided")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str, info: ValidationInfo) -> str:
        """Validate variable name format."""
        if not v.strip():
            raise ValueError("Variable name cannot be empty")
        if not v.isidentifier():
            raise ValueError("Variable name must be a valid Python identifier")
        return v


class PageTemplate(BaseModel):
    """Template for creating Notion pages."""

    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    parent_type: ParentType = Field(..., description="Type of parent container")
    properties: PageProperties = Field(..., description="Page property templates")
    content: Optional[List[BlockContent]] = Field(None, description="Page content templates")
    variables: List[TemplateVariable] = Field(default_factory=list, description="Template variables")

    def render(self, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Render the template with provided variables.

        Args:
            variables: Dictionary of variable values

        Returns:
            Dict containing rendered page data
        """
        # Validate required variables
        missing = [var.name for var in self.variables if var.required and var.name not in variables]
        if missing:
            raise ValueError(f"Missing required variables: {', '.join(missing)}")

        # Apply defaults for missing optional variables
        for var in self.variables:
            if var.name not in variables and var.default is not None:
                variables[var.name] = var.default

        # Render properties
        rendered_props = self.properties.dict()
        for key, value in rendered_props.items():
            if isinstance(value, str):
                for var_name, var_value in variables.items():
                    value = value.replace(f"{{{var_name}}}", str(var_value))
                rendered_props[key] = value

        # Render content blocks if present
        rendered_content = None
        if self.content:
            rendered_content = []
            for block in self.content:
                rendered_block = block.dict()
                if isinstance(rendered_block.get("text"), str):
                    for var_name, var_value in variables.items():
                        rendered_block["text"] = rendered_block["text"].replace(f"{{{var_name}}}", str(var_value))
                rendered_content.append(rendered_block)

        return {
            "properties": rendered_props,
            "content": rendered_content,
        }
