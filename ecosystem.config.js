module.exports = {
  apps: [
    {
      name: 'goni-backend',
      script: 'main.py',
      interpreter: '/home/ubuntu/goni/venv/bin/python',
      cwd: '/home/ubuntu/goni/back',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production'
      },
      error_file: '/home/ubuntu/goni/logs/backend-error.log',
      out_file: '/home/ubuntu/goni/logs/backend-out.log',
      log_file: '/home/ubuntu/goni/logs/backend-combined.log',
      time: true
    },
    {
      name: 'goni-frontend',
      script: 'npm',
      args: 'start',
      cwd: '/home/ubuntu/goni/front',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production'
      },
      error_file: '/home/ubuntu/goni/logs/frontend-error.log',
      out_file: '/home/ubuntu/goni/logs/frontend-out.log',
      log_file: '/home/ubuntu/goni/logs/frontend-combined.log',
      time: true
    }
  ]
};
