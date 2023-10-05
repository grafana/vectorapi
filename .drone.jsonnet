local repo = 'grafana/vectorapi';
local sha = '${DRONE_COMMIT_SHA:0:10}';
local repoWithSha = '%s:%s' % [repo, sha];
local pythonVersion = '3.11';

local vault_secret(name, vault_path, key) = {
  kind: 'secret',
  name: name,
  get: {
    path: vault_path,
    name: key,
  },
};

local step(name, commands, image) = {
  name: name,
  commands: commands,
  image: image,
};

local droneCacheSettings = {
  backend: 'gcs',
  bucket: 'drone-cache-mlops',
  region: 'us-central1',
  secret: {
    environment: {
      GCS_CACHE_JSON_KEY: { from_secret: 'gcs_service_account_key' },
    },
  },
};


local cached_step(cache_step, cache_key, mount, depends_on=[]) = [
  step('restore %s' % cache_step.name, [], image='meltwater/drone-cache') + droneCacheSettings.secret + {
    pull: true,
    settings: {
      backend: droneCacheSettings.backend,
      restore: true,
      cache_key: cache_key,
      archive_format: 'gzip',
      bucket: droneCacheSettings.bucket,
      region: droneCacheSettings.region,
      mount: mount,
    },
  },
  cache_step { depends_on: ['restore %s' % cache_step.name] + depends_on },
  step('store %s' % cache_step.name, [], image='meltwater/drone-cache') + droneCacheSettings.secret + {
    pull: true,
    settings: {
      backend: droneCacheSettings.backend,
      rebuild: true,
      override: false,
      cache_key: cache_key,
      archive_format: 'gzip',
      bucket: droneCacheSettings.bucket,
      region: droneCacheSettings.region,
      mount: mount,
    },
  } + { depends_on: [cache_step.name] },
];

local pipeline(name, steps=[], services=[], volumes=[]) = {
  kind: 'pipeline',
  type: 'docker',
  clone+: {
    retries: 3,
  },
  name: name,
  services: services,
  volumes: volumes,
  steps: steps,
  trigger+: {
    ref+: [
      'refs/heads/main',
      'refs/heads/public-docker-image',
    ],
  },
};

// Build and push Docker image (multi-arch)
local buildDockerPipeline(arch='amd64') = pipeline(
  name='docker-linux-%s' % arch,
  steps=[
    step('Build and push Docker image', [], 'plugins/docker') + {
      environment: {
        DOCKER_BUILDKIT: 1,
      },
      settings: {
        repo: repo,
        cache_from: repo,
        target: 'production',
        build_args: [
          'BUILDKIT_INLINE_CACHE=1',
        ],
        username: {
          from_secret: 'docker_username',
        },
        password: {
          from_secret: 'docker_password',
        },

        tags: [
          '${DRONE_COMMIT_SHA:0:10}-linux-%s' % arch,
        ],
      },
    },
  ],
);

// Push manifest for multi-arch image.
local dockerManifestPipeline = pipeline(
  name='docker-manifest',
  steps=[
    {
      name: 'manifest',
      image: 'plugins/manifest',
      username: {
        from_secret: 'docker_username',
      },
      password: {
        from_secret: 'docker_password',
      },
      target: repoWithSha,
      template: '%s-OS-ARCH' % repoWithSha,
      platforms: ['linux/amd64', 'linux/arm64'],
    },
  ],
) + {
  depends_on: [
    'docker-linux-amd64',
    'docker-linux-arm64',
  ],
};

// Tests and integration tests
local poetryWorkspaceHome = {
  POETRY_VERSION: '1.6.1',
  POETRY_VIRTUALENVS_IN_PROJECT: true,
  POETRY_HOME: '/drone/src/.poetry',
  POSTGRES_HOST: 'db',
  POSTGRES_PASSWORD: 'mysecretpassword',
  POSTGRES_PORT: 5432,
  POSTGRES_DB: 'postgres',
  VECTORAPI_STORE_SCHEMA: 'test_schema',
  VECTORAPI_STORE_CLIENT: 'pgvector',
};

local python_poetry_test_steps(depends_on=[]) =
  cached_step(
    step('setup poetry', [
      'curl -sSL https://install.python-poetry.org | python -',
    ], image='python:%s-bullseye' % pythonVersion) + { environment: poetryWorkspaceHome },
    cache_key='{{ os }}-{{ arch }}/py%s/poetry/%s' % [pythonVersion, poetryWorkspaceHome.POETRY_VERSION],
    mount=['.poetry'],
    depends_on=depends_on,
  ) +
  cached_step(
    step('setup python-venv', [
      'export PATH=$POETRY_HOME/bin:$PATH',
      'poetry install --sync',
    ], image='python:%s-bullseye' % pythonVersion) + { environment: poetryWorkspaceHome },
    cache_key='{{ os }}-{{ arch }}/py%s/python-venv/vectorapi/{{ checksum "poetry.lock" }}' % [pythonVersion],
    mount=['.venv'],
    depends_on=['setup poetry'],
  ) + [
    step('poetry lock check', [
      'export PATH=$POETRY_HOME/bin:$PATH',
      'poetry lock --check',
    ], image='python:%s-bullseye' % pythonVersion) + { environment: poetryWorkspaceHome, depends_on: ['setup python-venv'] },
    step('lint', [
      '. .venv/bin/activate',
      'make lint',
    ], image='python:%s-bullseye' % pythonVersion) + { depends_on: ['setup python-venv'] },
    step('static analysis', [
      '. .venv/bin/activate',
      'make static-analysis',
    ], image='python:%s-bullseye' % pythonVersion) + {
      environment: poetryWorkspaceHome,
      depends_on: ['setup python-venv'],
      //  ignore mypy failures for now
      failure: 'ignore',
    },
    step('test', [
      '. .venv/bin/activate',
      'make test',
    ], image='python:%s-bullseye' % pythonVersion) + { environment: poetryWorkspaceHome, depends_on: ['setup python-venv'] },
    step('integration', [
      '. .venv/bin/activate',
      'make test-integration',
    ], image='python:%s-bullseye' % pythonVersion) + { environment: poetryWorkspaceHome, depends_on: ['setup python-venv'] },
  ];


local pythonTestsPipeline = pipeline(
  name='Python tests',
  steps=python_poetry_test_steps(),
  services=[
    {
      name: 'db',
      image: 'ankane/pgvector',
      environment: {
        POSTGRES_USER: 'postgres',
        POSTGRES_PASSWORD: 'mysecretpassword',
        POSTGRES_PORT: 5432,
        POSTGRES_DB: 'postgres',
      },
    },
  ]
) + { trigger+: {
  ref+: [
    'refs/pull/**',
  ],
} };

// Output drone yaml
[
  // Pipelines
  buildDockerPipeline('amd64'),
  buildDockerPipeline('arm64'),
  dockerManifestPipeline,
  pythonTestsPipeline,
  // Secrets
  vault_secret('gcr_admin', 'infra/data/ci/gcr-admin', '.dockerconfigjson'),
  vault_secret('gcr_reader', 'secret/data/common/gcr', '.dockerconfigjson'),
  vault_secret('docker_username', 'infra/data/ci/docker_hub', 'username'),
  vault_secret('docker_password', 'infra/data/ci/docker_hub', 'password'),
  vault_secret('gcs_service_account_key', 'infra/data/ci/drone-plugins', 'gcp_key'),
]
