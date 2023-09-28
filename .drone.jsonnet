local repo = 'us.gcr.io/kubernetes-dev/vectorapi';
local repoWithSha = '%s:${DRONE_COMMIT_SHA:0:10}' % repo;

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
local dockerSock = {
  name: 'dockersock',
  path: '/var/run',
};

local dockerManifestPipeline = pipeline(
  name='docker-manifest',
  steps=[
    {
      name: 'manifest',
      image: 'docker:dind',
      volumes: [
        dockerSock,
      ],
      commands: [
        // wait for host Docker to start when using DinD (30s timeout)
        'counter=0; until [ $counter -gt 30 ] || [ $(docker ps > /dev/null 2>&1; echo $?) -eq 0 ]; do sleep 1; let counter+=1;  echo "($counter) waiting for docker to start.."; done',
        'mkdir -p ~/.docker',
        'echo $dockerconfigjson > ~/.docker/config.json',
        // push commit tag manifest
        'docker manifest create %s %s-linux-amd64 %s-linux-arm64' % [repoWithSha, repoWithSha, repoWithSha],
        'docker manifest push %s' % repoWithSha,
        // push latest tag manifest
        'docker manifest create %s:latest %s-linux-amd64 %s-linux-arm64' % [repo, repoWithSha, repoWithSha],
        'docker manifest push %s:latest' % repo,
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
  services=[
    {
      name: 'docker',
      image: 'docker:dind',
      privileged: true,
      volumes: [
        dockerSock,
      ],
    },
  ],
  volumes=[
    {
      name: 'dockersock',
      temp: {},
    },
  ]
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
