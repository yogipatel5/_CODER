"""
Tool for creating pages from templates.
"""

from typing import Any, ClassVar, Dict, List, Optional, Type

from pydantic import BaseModel, Field

from notion.tools.base import NotionBaseTool
from notion.tools.models.page import PageResponse
from notion.tools.models.template import TemplateVariable


class CreateTemplateArgs(BaseModel):
    """Arguments for creating a page from template."""

    parent_id: str = Field(..., description="ID of the parent page")
    template_id: str = Field(..., description="ID of the template page")
    variables: List[TemplateVariable] = Field(..., description="Template variables")


class CreateTemplatePageTool(NotionBaseTool):
    """Tool for creating pages from templates."""

    name: ClassVar[str] = "create_template_page"
    description: ClassVar[str] = "Create a new page from a template in Notion"
    args_schema: ClassVar[Type[BaseModel]] = CreateTemplateArgs

    def run(self, parent_id: str, template_id: str, variables: List[TemplateVariable], **kwargs: Any) -> Dict[str, Any]:
        """Create a new page from a template with variable substitution.

        Args:
            parent_id: ID of the parent page.
            template_id: ID of the template page.
            variables: List of template variables to substitute.
            **kwargs: Additional arguments.

        Returns:
            Dict containing operation status and created page data.
        """
        try:
            # Get template page content
            template = self.api.pages.retrieve(page_id=template_id)

            # Apply template variables
            properties = template.get("properties", {})
            for var in variables:
                if var.name in properties:
                    properties[var.name]["title"][0]["text"]["content"] = var.value

            # Create page from template
            response = self.api.pages.create(
                parent={"type": "page_id", "page_id": parent_id},
                properties=properties,
            )

            # Return success response even if we can't parse the response
            if not isinstance(response, dict):
                return {
                    "success": True,
                    "message": "Page created from template successfully",
                    "data": {"id": str(response)},
                }

            try:
                page_response = PageResponse(**response)
                return {
                    "success": True,
                    "message": f"Page '{page_response.title}' created from template successfully",
                    "data": page_response.model_dump(),
                }
            except Exception as parse_error:
                return {
                    "success": True,
                    "message": "Page created from template successfully but couldn't parse response",
                    "data": response,
                    "error": str(parse_error),
                }

        except Exception as e:
            return self._handle_api_error(e, "create template page")
