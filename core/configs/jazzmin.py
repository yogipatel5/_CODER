"""Jazzmin admin interface configuration."""

JAZZMIN_SETTINGS = {
    "site_title": "Admin Portal",
    "site_header": "Admin Portal",
    "site_brand": "Admin Portal",
    "welcome_sign": "Welcome to the Admin Portal",
    "copyright": "CODER",
    "search_model": "auth.User",
    "user_avatar": None,
    # Custom icons for side menu apps and models
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "shared.task": "fas fa-tasks",
        "shared.taskerror": "fas fa-exclamation-triangle",
        "dhcp_routes": "fas fa-network-wired",
    },
    # UI Customizer
    "show_ui_builder": False,
    # Additional UI customizations
    "show_sidebar": True,
    "navigation_expanded": False,
    "changeform_format": "horizontal_tabs",
    # UI Themes - Using a cleaner theme
    "ui_theme": {
        "navbar": "navbar-dark",
        "no_navbar_border": True,
        "sidebar": "sidebar-dark-primary",
        "brand_colour": "navbar-primary",
        "accent": "accent-primary",
        "navbar_small_text": False,
        "sidebar_nav_small_text": False,
        "sidebar_disable_expand": False,
        "sidebar_nav_child_indent": True,
        "sidebar_nav_compact_style": True,
        "sidebar_nav_legacy_style": False,
        "sidebar_nav_flat_style": False,
        "theme": "flatly",
    },
}

# Additional Jazzmin UI Customization
JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-primary",
    "accent": "accent-primary",
    "navbar": "navbar-dark",
    "no_navbar_border": True,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": True,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": True,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "flatly",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success",
    },
}
