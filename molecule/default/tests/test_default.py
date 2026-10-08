"""Testinfra verification tests for Molecule integration strategy."""

def test_common_packages_installed(host):
    """Verify git, jq, curl, ripgrep are installed."""
    for pkg in ["git", "jq", "curl", "ca-certificates", "ripgrep"]:
        assert host.package(pkg).is_installed


def test_neovim_binary_executable(host):
    """Verify Neovim binary exists and is executable."""
    nvim = host.file("/usr/local/bin/nvim")
    assert nvim.exists
    assert nvim.is_file
    cmd = host.run("nvim --version")
    assert cmd.rc == 0
    assert "NVIM" in cmd.stdout


def test_docker_gpg_key(host):
    """Verify Docker GPG key file exists."""
    gpg_key = host.file("/etc/apt/keyrings/docker.asc")
    assert gpg_key.exists


def test_docker_group_membership(host):
    """Verify docker group exists and user debrutal is added."""
    assert host.group("docker").exists
    user = host.user("debrutal")
    if user.exists:
        assert "docker" in user.groups


def test_traefik_directories_and_permissions(host):
    """Verify Traefik directories and acme.json permissions."""
    traefik_dir = host.file("/opt/traefik")
    assert traefik_dir.exists
    assert traefik_dir.is_directory

    acme_file = host.file("/opt/traefik/acme/acme.json")
    assert acme_file.exists
    assert acme_file.is_file
    assert oct(acme_file.mode) == "0o600"


def test_traefik_static_config(host):
    """Verify traefik.yml static configuration contents."""
    traefik_yml = host.file("/opt/traefik/traefik.yml")
    assert traefik_yml.exists
    content = traefik_yml.content_string
    assert "dnsChallenge:" in content
    assert "provider: cloudflare" in content
    assert "admin@debrutal.dev" in content
    assert "aliasHeadersStrategy: \"delete\"" in content
    assert "encodedCharacters:" in content
    assert "allowEncodedSlash: false" in content
    assert "caServer" not in content


def test_traefik_docker_compose_config(host):
    """Verify docker-compose.yml contains DNS environment and wildcard router rules."""
    compose_yml = host.file("/opt/traefik/docker-compose.yml")
    assert compose_yml.exists
    content = compose_yml.content_string
    assert "CF_DNS_API_TOKEN=" in content
    assert "mini.debrutal.dev" in content
    assert "*.mini.debrutal.dev" in content
    assert "staging.kita-kit.de" in content
    assert "*.staging.kita-kit.de" in content
    assert "host.docker.internal:host-gateway" in content


def test_traefik_dynamic_config(host):
    """Verify dynamic_conf.yml contains defaultGeneratedCert for *.mini.debrutal.dev."""
    dynamic_yml = host.file("/opt/traefik/dynamic/dynamic_conf.yml")
    assert dynamic_yml.exists
    content = dynamic_yml.content_string
    assert "defaultGeneratedCert:" in content
    assert "mini.debrutal.dev" in content
    assert "*.mini.debrutal.dev" in content



def test_lago_directory_and_compose(host):
    """Verify Lago directory and docker-compose.yml file."""
    lago_dir = host.file("/opt/lago")
    assert lago_dir.exists
    assert lago_dir.is_directory

    compose_yml = host.file("/opt/lago/docker-compose.yml")
    assert compose_yml.exists
    content = compose_yml.content_string
    assert "traefik.enable=true" in content
    assert "lago.mini.debrutal.dev" in content
    assert "lago-api.mini.debrutal.dev" in content
    assert "LAGO_RSA_PRIVATE_KEY:" in content


def test_invoiceninja_directory_and_compose(host):
    """Verify Invoice Ninja directory, nginx config, and docker-compose.yml file."""
    inv_dir = host.file("/opt/invoiceninja")
    assert inv_dir.exists
    assert inv_dir.is_directory

    vhost_conf = host.file("/opt/invoiceninja/in-vhost.conf")
    assert vhost_conf.exists

    compose_yml = host.file("/opt/invoiceninja/docker-compose.yml")
    assert compose_yml.exists
    content = compose_yml.content_string
    assert "traefik.enable=true" in content
    assert "invoiceninja.mini.debrutal.dev" in content
    assert "APP_KEY:" in content


def test_espocrm_directory_and_compose(host):
    """Verify EspoCRM directory and docker-compose.yml file."""
    espo_dir = host.file("/opt/espocrm")
    assert espo_dir.exists
    assert espo_dir.is_directory

    compose_yml = host.file("/opt/espocrm/docker-compose.yml")
    assert compose_yml.exists
    content = compose_yml.content_string
    assert "traefik.enable=true" in content
    assert "espocrm.mini.debrutal.dev" in content
    assert "ESPOCRM_DATABASE_PLATFORM:" in content


def test_uptime_kuma_directory_and_compose(host):
    """Verify Uptime Kuma directory, autokuma config, and docker-compose.yml file."""
    kuma_dir = host.file("/opt/uptime-kuma")
    assert kuma_dir.exists
    assert kuma_dir.is_directory

    autokuma_conf = host.file("/opt/uptime-kuma/autokuma-config.toml")
    assert autokuma_conf.exists

    compose_yml = host.file("/opt/uptime-kuma/docker-compose.yml")
    assert compose_yml.exists
    content = compose_yml.content_string
    assert "traefik.enable=true" in content
    assert "status.mini.debrutal.dev" in content
    assert "autokuma" in content


def test_sentry_directory_and_compose(host):
    """Verify Sentry directory and docker-compose.yml file."""
    sentry_dir = host.file("/opt/sentry")
    assert sentry_dir.exists
    assert sentry_dir.is_directory

    compose_yml = host.file("/opt/sentry/docker-compose.yml")
    assert compose_yml.exists
    content = compose_yml.content_string
    assert "traefik.enable=true" in content
    assert "sentry.mini.debrutal.dev" in content
    assert "SECRET_KEY:" in content


def test_homepage_directory_and_compose(host):
    """Verify Homepage directory, configs, and docker-compose.yml file."""
    hp_dir = host.file("/opt/homepage")
    assert hp_dir.exists
    assert hp_dir.is_directory

    settings_yml = host.file("/opt/homepage/config/settings.yaml")
    assert settings_yml.exists

    services_yml = host.file("/opt/homepage/config/services.yaml")
    assert services_yml.exists
    assert "BookOrbit" in services_yml.content_string
    assert "Pinchflat" in services_yml.content_string
    assert "eBook2Audiobook" in services_yml.content_string


    compose_yml = host.file("/opt/homepage/docker-compose.yml")
    assert compose_yml.exists
    content = compose_yml.content_string
    assert "traefik.enable=true" in content
    assert "dash.mini.debrutal.dev" in content
    assert "homepage" in content
    assert "HOMEPAGE_ALLOWED_HOSTS" in content
    assert "kuma.homepage.http.name=" in content


def test_lgtm_directory_and_compose(host):
    """Verify LGTM stack directory, configs, and docker-compose.yml file."""
    lgtm_dir = host.file("/opt/lgtm")
    assert lgtm_dir.exists
    assert lgtm_dir.is_directory

    loki_conf = host.file("/opt/lgtm/loki-config.yaml")
    assert loki_conf.exists

    prom_conf = host.file("/opt/lgtm/prometheus.yml")
    assert prom_conf.exists

    tempo_conf = host.file("/opt/lgtm/tempo-config.yaml")
    assert tempo_conf.exists

    otel_conf = host.file("/opt/lgtm/otel-collector-config.yaml")
    assert otel_conf.exists
    otel_content = otel_conf.content_string
    assert "otlp/tempo" in otel_content
    assert "spanmetrics" in otel_content
    assert "tempo:4317" in otel_content

    compose_yml = host.file("/opt/lgtm/docker-compose.yml")
    assert compose_yml.exists
    content = compose_yml.content_string
    assert "traefik.enable=true" in content
    assert "grafana.mini.debrutal.dev" in content
    assert "grafana/loki" in content
    assert "grafana/tempo" in content
    assert "prom/prometheus" in content
    assert "GF_AUTH_GENERIC_OAUTH_ENABLED:" in content
    assert "GF_AUTH_GENERIC_OAUTH_CLIENT_ID:" in content
    assert "otel-collector" in content
    assert "cadvisor" in content
    assert "otel/opentelemetry-collector-contrib" in content
    assert "gcr.io/cadvisor/cadvisor" in content


def test_lgtm_prometheus_scrape_targets(host):
    """Verify Prometheus config includes OTEL and cAdvisor scrape targets."""
    prom_conf = host.file("/opt/lgtm/prometheus.yml")
    assert prom_conf.exists
    content = prom_conf.content_string
    assert "otel-collector" in content
    assert "otel-span-metrics" in content
    assert "cadvisor" in content
    assert "authentik" in content


def test_lgtm_datasource_uids(host):
    """Verify Grafana datasources have UIDs set for dashboard cross-references."""
    ds_conf = host.file("/opt/lgtm/grafana/provisioning/datasources/datasources.yaml")
    assert ds_conf.exists
    content = ds_conf.content_string
    assert "uid: prometheus" in content
    assert "uid: loki" in content
    assert "uid: tempo" in content


def test_lgtm_dashboard_provisioned(host):
    """Verify Grafana dashboard JSON is provisioned."""
    dashboard_dir = host.file("/opt/lgtm/grafana/provisioning/dashboards/json")
    assert dashboard_dir.exists
    assert dashboard_dir.is_directory

    dashboard = host.file("/opt/lgtm/grafana/provisioning/dashboards/json/mini-overview.json")
    assert dashboard.exists
    content = dashboard.content_string
    assert "Mini Server Overview" in content
    assert "mini-overview" in content
    assert "cadvisor" in content.lower() or "container_cpu" in content
    assert "traefik" in content.lower()
    assert "span_metrics" in content


def test_lgtm_promtail_enhanced(host):
    """Verify Promtail config has enhanced labels and log level extraction."""
    promtail_conf = host.file("/opt/lgtm/promtail-config.yaml")
    assert promtail_conf.exists
    content = promtail_conf.content_string
    assert "compose_project" in content
    assert "compose_service" in content
    assert "pipeline_stages" in content
    assert "log_level" in content


def test_traefik_otel_config(host):
    """Verify Traefik static config includes OTEL tracing."""
    traefik_yml = host.file("/opt/traefik/traefik.yml")
    assert traefik_yml.exists
    content = traefik_yml.content_string
    assert "tracing:" in content
    assert "otel-collector:4317" in content
    assert "insecure: true" in content


def test_gitea_otel_env_vars(host):
    """Verify Gitea docker-compose includes OTEL environment variables."""
    compose_yml = host.file("/opt/gitea/docker-compose.yml")
    assert compose_yml.exists
    content = compose_yml.content_string
    assert "GITEA__opentelemetry__ENABLED=true" in content
    assert "GITEA__opentelemetry__ENDPOINT=otel-collector:4317" in content
    assert "GITEA__opentelemetry__SERVICE_NAME=gitea" in content


def test_authentik_metrics_enabled(host):
    """Verify Authentik docker-compose includes metrics endpoint."""
    compose_yml = host.file("/opt/authentik/docker-compose.yml")
    assert compose_yml.exists
    content = compose_yml.content_string
    assert "AUTHENTIK_LISTEN__METRICS" in content


def test_lago_otel_env_vars(host):
    """Verify Lago docker-compose includes OTEL environment variables."""
    compose_yml = host.file("/opt/lago/docker-compose.yml")
    assert compose_yml.exists
    content = compose_yml.content_string
    assert "OTEL_SERVICE_NAME" in content
    assert "otel-collector" in content


def test_sentry_otel_env_vars(host):
    """Verify Sentry docker-compose includes OTEL environment variables."""
    compose_yml = host.file("/opt/sentry/docker-compose.yml")
    assert compose_yml.exists
    content = compose_yml.content_string
    assert "OTEL_SERVICE_NAME" in content
    assert "otel-collector" in content


def test_agentzero_directory_and_compose(host):
    """Verify Agent Zero containerized directory and docker-compose.yml configuration."""
    az_dir = host.file("/opt/agentzero")
    assert az_dir.exists
    assert az_dir.is_directory

    usr_dir = host.file("/opt/agentzero/usr")
    assert usr_dir.exists
    assert usr_dir.is_directory

    compose_yml = host.file("/opt/agentzero/docker-compose.yml")
    assert compose_yml.exists
    content = compose_yml.content_string
    assert "traefik.enable=true" in content
    assert "agentzero.mini.debrutal.dev" in content
    assert "agent0ai/agent-zero" in content


def test_pinchflat_directory_and_compose(host):
    """Verify Pinchflat containerized directory and docker-compose.yml configuration."""
    pf_dir = host.file("/opt/pinchflat")
    assert pf_dir.exists
    assert pf_dir.is_directory

    config_dir = host.file("/opt/pinchflat/config")
    assert config_dir.exists
    assert config_dir.is_directory

    downloads_dir = host.file("/opt/pinchflat/downloads")
    assert downloads_dir.exists
    assert downloads_dir.is_directory

    compose_yml = host.file("/opt/pinchflat/docker-compose.yml")
    assert compose_yml.exists
    content = compose_yml.content_string
    assert "traefik.enable=true" in content
    assert "pinchflat.mini.debrutal.dev" in content
    assert "ghcr.io/kieraneglin/pinchflat" in content
    assert "traefik.http.routers.pinchflat.middlewares=authentik@file" in content


def test_ebook2audiobook_directory_and_compose(host):
    """Verify eBook2Audiobook containerized directory and docker-compose.yml configuration."""
    eb_dir = host.file("/opt/ebook2audiobook")
    assert eb_dir.exists
    assert eb_dir.is_directory

    for subdir in ["ebooks", "audiobooks", "models", "voices", "tmp"]:
        d = host.file(f"/opt/ebook2audiobook/{subdir}")
        assert d.exists
        assert d.is_directory

    compose_yml = host.file("/opt/ebook2audiobook/docker-compose.yml")
    assert compose_yml.exists
    content = compose_yml.content_string
    assert "traefik.enable=true" in content
    assert "ebook2audiobook.mini.debrutal.dev" in content
    assert "athomasson2/ebook2audiobook" in content
    assert "traefik.http.routers.ebook2audiobook.middlewares=authentik@file" in content


def test_restic_backup_setup(host):
    """Verify Restic backup directories, configuration, scripts, and systemd units."""
    for path in ["/backup", "/backup/dumps", "/etc/restic"]:
        d = host.file(path)
        assert d.exists
        assert d.is_directory

    pwd_file = host.file("/etc/restic/password")
    assert pwd_file.exists
    assert pwd_file.mode == 0o600

    env_file = host.file("/etc/restic/env.sh")
    assert env_file.exists
    assert env_file.mode == 0o600
    assert "RESTIC_REPOSITORY" in env_file.content_string

    backup_sh = host.file("/usr/local/bin/restic-backup.sh")
    assert backup_sh.exists
    assert backup_sh.mode == 0o755
    content = backup_sh.content_string
    assert "authentik-db" in content
    assert "bookorbit-db" in content
    assert "gitea.db" in content
    assert "restic backup" in content

    cli_helper = host.file("/usr/local/bin/restic-infra")
    assert cli_helper.exists
    assert cli_helper.mode == 0o755

    svc = host.file("/etc/systemd/system/restic-backup.service")
    assert svc.exists
    timer = host.file("/etc/systemd/system/restic-backup.timer")
    assert timer.exists

