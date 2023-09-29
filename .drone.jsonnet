local repo = 'us.gcr.io/kubernetes-dev/vectorapi';
local sha = '${DRONE_COMMIT_SHA:0:10}';
local repoWithSha = '%s:%s' % [repo, sha];

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
      'refs/heads/drone-manifest-without-dind',  // temporary, remove after testing
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
        config: {
          from_secret: 'gcr_admin',
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
      image: 'mplatform/manifest-tool:alpine',
      commands: [
        'mkdir -p ~/.docker',
        'echo $dockerconfigjson > ~/.docker/config.json',
        'manifest-tool push from-args --platforms linux/amd64,linux/arm64 --template %s-OS-ARCH --tags latest --target %s' % [repoWithSha, repoWithSha],
      ],
      environment: {
        COMPOSE_DOCKER_CLI_BUILD: 1,
        DOCKER_BUILDKIT: 1,
        dockerconfigjson: {
          from_secret: 'gcr_admin',
        },
      },
    },
  ],
) + {
  depends_on: [
    'docker-linux-amd64',
    'docker-linux-arm64',
  ],
};

// Tests and integration tests
local integrationTestsPipeline = pipeline(
  name='Tests',
  steps=[
    {
      name: 'Build and run tests',
      image: 'python:3.11-bullseye',
      commands: [
        'curl -sSL https://install.python-poetry.org | python -',
        'export PATH=$POETRY_HOME/bin:$PATH',
        'poetry install',
        // TODO: share env setup and split these 2 tests into separate step
        'make test',
        'make test-integration',
      ],
      environment: {
        POETRY_VERSION: '1.6.1',
        POETRY_VIRTUALENVS_CREATE: false,
        POETRY_HOME: '/drone/src/.poetry',
        POSTGRES_HOST: 'db',
        POSTGRES_PASSWORD: 'mysecretpassword',
        POSTGRES_PORT: 5432,
        POSTGRES_DB: 'postgres',
        VECTORAPI_STORE_SCHEMA: 'test_schema',
        VECTORAPI_STORE_CLIENT: 'pgvector',
      },
    },
  ],
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
  integrationTestsPipeline,
  // Secrets
  vault_secret('gcr_admin', 'infra/data/ci/gcr-admin', '.dockerconfigjson'),
  vault_secret('gcr_reader', 'secret/data/common/gcr', '.dockerconfigjson'),
]
