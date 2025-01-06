"""Forms for GitHub repository management."""

from typing import Any, Dict, List, Optional

from django import forms


class RepositoryForm(forms.Form):
    """Form for creating and editing repositories."""

    name = forms.CharField(
        max_length=100,
        help_text="Repository name should be lowercase, with no spaces.",
        widget=forms.TextInput(attrs={"placeholder": "my-awesome-project"}),
    )
    description = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(
            attrs={"rows": 3, "placeholder": "A brief description of your project"}
        ),
        help_text="A short description that will be displayed on your repository's main page.",
    )
    visibility = forms.ChoiceField(
        choices=[("public", "Public"), ("private", "Private")],
        initial="private",
        help_text="Public repositories are visible to everyone. Private repositories are only visible to you and collaborators.",
    )
    template = forms.ChoiceField(
        required=False,
        help_text="Choose a template to initialize your repository with some basic files and directories.",
    )
    initial_branch = forms.CharField(
        max_length=100,
        initial="main",
        help_text="The name of the default branch. Common choices are 'main' or 'master'.",
    )

    def __init__(self, *args, **kwargs):
        """Initialize form with dynamic template choices."""
        super().__init__(*args, **kwargs)
        self.fields["template"].choices = self._get_template_choices()

    def _get_template_choices(self) -> List[tuple[str, str]]:
        """Get available repository templates."""
        try:
            # TODO: Implement template listing using GitHub API
            return [("", "No template")]
        except Exception:
            return [("", "No template")]  # Fallback if template listing fails

    def clean_name(self) -> str:
        """Validate repository name."""
        name = self.cleaned_data["name"]
        if " " in name:
            raise forms.ValidationError("Repository name cannot contain spaces.")
        if not name.islower():
            raise forms.ValidationError("Repository name must be lowercase.")
        if name.startswith(".") or name.endswith("."):
            raise forms.ValidationError(
                "Repository name cannot start or end with a period."
            )
        return name

    def clean_initial_branch(self) -> str:
        """Validate initial branch name."""
        branch = self.cleaned_data["initial_branch"]
        if " " in branch:
            raise forms.ValidationError("Branch name cannot contain spaces.")
        if branch.startswith(".") or branch.endswith("."):
            raise forms.ValidationError(
                "Branch name cannot start or end with a period."
            )
        return branch


class RepositoryFilterForm(forms.Form):
    """Form for filtering repository list."""

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Search repositories..."}),
    )
    visibility = forms.ChoiceField(
        choices=[("", "All"), ("public", "Public"), ("private", "Private")],
        required=False,
    )
    sort = forms.ChoiceField(
        choices=[
            ("name", "Name"),
            ("-updated", "Last Updated"),
            ("created", "Created Date"),
        ],
        required=False,
        initial="name",
    )

    def filter_repositories(
        self, repositories: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Filter repositories based on form data."""
        if not self.is_valid():
            return repositories

        filtered = repositories

        # Apply search filter
        if search := self.cleaned_data.get("search"):
            search = search.lower()
            filtered = [
                repo
                for repo in filtered
                if search in repo["name"].lower()
                or search in (repo.get("description", "").lower() or "")
            ]

        # Apply visibility filter
        if visibility := self.cleaned_data.get("visibility"):
            filtered = [repo for repo in filtered if repo["visibility"] == visibility]

        # Apply sorting
        if sort := self.cleaned_data.get("sort"):
            reverse = sort.startswith("-")
            key = sort[1:] if reverse else sort
            filtered = sorted(
                filtered, key=lambda x: str(x.get(key, "")), reverse=reverse
            )

        return filtered


class RepositoryDeleteForm(forms.Form):
    """Form for confirming repository deletion."""

    confirm_name = forms.CharField(
        help_text="Please type the repository name to confirm deletion.",
    )

    def __init__(self, *args, repository_name: Optional[str] = None, **kwargs):
        """Initialize form with repository name for validation."""
        super().__init__(*args, **kwargs)
        self.repository_name = repository_name

    def clean_confirm_name(self) -> str:
        """Validate confirmation name matches repository name."""
        confirm_name = self.cleaned_data["confirm_name"]
        if not self.repository_name:
            raise forms.ValidationError("No repository name provided for validation.")
        if confirm_name != self.repository_name:
            raise forms.ValidationError(
                "Please type the exact repository name to confirm deletion."
            )
        return confirm_name
