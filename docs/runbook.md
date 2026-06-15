# Harbor Runbook

## 本地启动

进入项目目录：

cd /workspaces/harbor

安装当前项目：

python -m pip install -e .

启动 Harbor：

python -m harbor.main

或者：

bash scripts/run_local.sh

## 运行测试

python -m unittest discover -s tests

或者：

bash scripts/test.sh

## 查看日志

日志文件位置：

data/logs/harbor.log
