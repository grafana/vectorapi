local repo = 'us.gcr.io/kubernetes-dev/vectorapi';
local repoWithSha = '%s:${DRONE_COMMIT_SHA:0:10}' % repo;
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
      'ruff check -v .',
    ], image='python:%s-bullseye' % pythonVersion) + { depends_on: ['setup python-venv'] },
    step('static analysis', [
      '. .venv/bin/activate',
      'mypy .',
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
  vault_secret('gcs_service_account_key', 'infra/data/ci/drone-plugins', 'gcp_key'),
]
