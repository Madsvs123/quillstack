"""Central registry of QuillStack apps for docs, admin, and tooling."""

QUILLSTACK_APPS = [
    {
        "key": "common",
        "label": "Common",
        "django": "apps.common",
        "frontend": "features/common",
        "apis": [],
    },
    {
        "key": "accounts",
        "label": "Accounts",
        "django": "apps.accounts",
        "frontend": "features/accounts",
        "apis": ["/api/v1/auth/"],
    },
    {
        "key": "tenancy",
        "label": "Tenancy",
        "django": "apps.tenancy",
        "frontend": "features/tenancy",
        "apis": ["/api/v1/tenancy/"],
    },
    {
        "key": "content",
        "label": "Content",
        "django": "apps.content",
        "frontend": "features/content",
        "apis": ["/api/v1/content/"],
    },
    {
        "key": "editorial",
        "label": "Editorial",
        "django": "apps.editorial",
        "frontend": "features/editorial",
        "apis": ["/api/v1/editorial/"],
    },
    {
        "key": "media_library",
        "label": "Media",
        "django": "apps.media_library",
        "frontend": "features/media",
        "apis": ["/api/v1/media/"],
    },
    {
        "key": "scheduling",
        "label": "Scheduling",
        "django": "apps.scheduling",
        "frontend": "features/scheduling",
        "apis": ["/api/v1/scheduling/"],
    },
    {
        "key": "delivery",
        "label": "Delivery",
        "django": "apps.delivery",
        "frontend": "features/delivery",
        "apis": ["/api/v1/delivery/", "/graphql/"],
    },
    {
        "key": "i18n_cms",
        "label": "i18n",
        "django": "apps.i18n_cms",
        "frontend": "features/i18n",
        "apis": ["/api/v1/i18n/"],
    },
    {
        "key": "search",
        "label": "Search",
        "django": "apps.search",
        "frontend": "features/search",
        "apis": ["/api/v1/search/"],
    },
    {
        "key": "analytics",
        "label": "Analytics",
        "django": "apps.analytics",
        "frontend": "features/analytics",
        "apis": ["/api/v1/analytics/"],
    },
    {
        "key": "notifications",
        "label": "Notifications",
        "django": "apps.notifications",
        "frontend": "features/notifications",
        "apis": ["/api/v1/notifications/", "/ws/user-notifications/"],
    },
    {
        "key": "webhooks",
        "label": "Webhooks",
        "django": "apps.webhooks",
        "frontend": "features/webhooks",
        "apis": ["/api/v1/webhooks/"],
    },
    {
        "key": "collaboration",
        "label": "Collaboration",
        "django": "apps.collaboration",
        "frontend": "features/collaboration",
        "apis": ["/api/v1/collaboration/", "/ws/collaborate/<id>/"],
    },
]


def app_keys() -> list[str]:
    return [a["label"] for a in QUILLSTACK_APPS]


def frontend_mirrors() -> dict[str, str]:
    return {a["frontend"]: a["key"] for a in QUILLSTACK_APPS}
