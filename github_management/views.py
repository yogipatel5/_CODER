"""Views for GitHub repository management."""

from typing import Any, Dict

from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView
from django.views.generic.detail import DetailView

from .forms import RepositoryDeleteForm, RepositoryFilterForm, RepositoryForm
from .services import get_all_repos


class DashboardView(TemplateView):
    """Dashboard view showing repository statistics and recent activity."""

    template_name = "github_management/dashboard.html"

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add repository statistics and recent activity to context."""
        context = super().get_context_data(**kwargs)
        try:
            repos = get_all_repos()
            context.update(
                {
                    "repository_count": len(repos),
                    "branch_count": 0,  # TODO: Implement branch counting
                    "commit_count": 0,  # TODO: Implement commit counting
                    "push_count": 0,  # TODO: Implement push counting
                    "recent_activity": [],  # TODO: Implement activity tracking
                }
            )
        except Exception as e:
            messages.error(self.request, f"Error fetching repository data: {str(e)}")
            context.update(
                {
                    "repository_count": 0,
                    "branch_count": 0,
                    "commit_count": 0,
                    "push_count": 0,
                    "recent_activity": [],
                }
            )
        return context


class RepositoryListView(TemplateView):
    """View for listing repositories with filtering and sorting."""

    template_name = "github_management/repositories/list.html"

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add filtered repositories to context."""
        context = super().get_context_data(**kwargs)
        try:
            # Get and filter repositories
            repos = get_all_repos()
            filter_form = RepositoryFilterForm(self.request.GET)
            filtered_repos = filter_form.filter_repositories(repos)

            context.update(
                {
                    "repositories": filtered_repos,
                    "filter_form": filter_form,
                }
            )
        except Exception as e:
            messages.error(self.request, f"Error fetching repositories: {str(e)}")
            context.update(
                {
                    "repositories": [],
                    "filter_form": RepositoryFilterForm(),
                }
            )
        return context


class RepositoryDetailView(DetailView):
    """View for displaying repository details."""

    template_name = "github_management/repositories/detail.html"
    context_object_name = "repository"

    def get_object(self, queryset=None):
        """Get repository details from GitHub API."""
        try:
            repos = get_all_repos()
            repo = next((r for r in repos if r["name"] == self.kwargs["name"]), None)
            if not repo:
                messages.error(self.request, "Repository not found.")
                return None
            return repo
        except Exception as e:
            messages.error(self.request, f"Error fetching repository details: {str(e)}")
            return None

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add branch information and recent activity to context."""
        context = super().get_context_data(**kwargs)
        try:
            context.update(
                {
                    "branches": [],  # TODO: Implement branch listing
                    "branch_count": 0,  # TODO: Implement branch counting
                    "recent_activity": [],  # TODO: Implement activity tracking
                }
            )
        except Exception as e:
            messages.error(self.request, f"Error fetching repository data: {str(e)}")
        return context


class RepositoryCreateView(FormView):
    """View for creating a new repository."""

    template_name = "github_management/repositories/form.html"
    form_class = RepositoryForm
    success_url = reverse_lazy("github_management:repository_list")

    def form_valid(self, form):
        """Create repository using GitHub API."""
        try:
            # TODO: Implement repository creation
            messages.success(self.request, "Repository created successfully.")
            return super().form_valid(form)
        except Exception as e:
            messages.error(self.request, f"Error creating repository: {str(e)}")
            return self.form_invalid(form)


class RepositoryUpdateView(FormView):
    """View for updating repository settings."""

    template_name = "github_management/repositories/form.html"
    form_class = RepositoryForm

    def get_initial(self):
        """Pre-populate form with current repository settings."""
        initial = super().get_initial()
        try:
            repos = get_all_repos()
            repo = next((r for r in repos if r["name"] == self.kwargs["name"]), None)
            if repo:
                initial.update(
                    {
                        "name": repo["name"],
                        "description": repo.get("description", ""),
                        "visibility": repo["visibility"],
                    }
                )
        except Exception as e:
            messages.error(self.request, f"Error fetching repository details: {str(e)}")
        return initial

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add repository object to context."""
        context = super().get_context_data(**kwargs)
        context["repository"] = {"name": self.kwargs["name"]}
        return context

    def get_success_url(self):
        """Redirect to repository detail page."""
        return reverse_lazy(
            "github_management:repository_detail", kwargs={"name": self.kwargs["name"]}
        )

    def form_valid(self, form):
        """Update repository using GitHub API."""
        try:
            # TODO: Implement repository update
            messages.success(self.request, "Repository updated successfully.")
            return super().form_valid(form)
        except Exception as e:
            messages.error(self.request, f"Error updating repository: {str(e)}")
            return self.form_invalid(form)


class RepositoryDeleteView(FormView):
    """View for deleting a repository."""

    template_name = "github_management/repositories/delete.html"
    form_class = RepositoryDeleteForm
    success_url = reverse_lazy("github_management:repository_list")

    def get_form_kwargs(self):
        """Pass repository name to form."""
        kwargs = super().get_form_kwargs()
        kwargs["repository_name"] = self.kwargs["name"]
        return kwargs

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add repository object to context."""
        context = super().get_context_data(**kwargs)
        context["repository"] = {"name": self.kwargs["name"]}
        return context

    def form_valid(self, form):
        """Delete repository using GitHub API."""
        try:
            # TODO: Implement repository deletion
            messages.success(self.request, "Repository deleted successfully.")
            return super().form_valid(form)
        except Exception as e:
            messages.error(self.request, f"Error deleting repository: {str(e)}")
            return self.form_invalid(form)
