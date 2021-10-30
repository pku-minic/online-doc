# 5.3. 本地测试

很多情况下, 在评测系统中进行在线评测会消耗更多的时间, 而我们又会对程序进行一些微调, 并观察其运行结果. 考虑到这种需求, 我们提供了一系列开放的功能/性能测试用例, 同时提供了与评测机环境相同的 Docker 镜像, 供大家进行本地测试.

## 获取开放测试用例

我们已经将公开的测试用例上传到了 GitHub ([open-test-cases](https://github.com/pku-minic/open-test-cases)), 你可以 clone 该 repo:

```
$ git clone --recursive https://github.com/pku-minic/open-test-cases.git
```

repo 中包含若干目录:

* `sysy` 目录: 大赛公开的 SysY 功能/性能测试.
* `eeyore` 目录: 公开的 Eeyore 功能/性能测试, 输入/输出与 SysY 测试用例相同.
* `tigger` 目录: 公开的 Tigger 功能/性能测试, 输入/输出与 SysY 测试用例相同.
* `risc-v` 目录: 可构建 RISC-V 开发环境的 Dockerfile.

## 获取评测机环境的 Docker 镜像

你可以在 GitHub 上的 [`pku-minic/oj-docker`](https://github.com/pku-minic/oj-docker) 仓库中获取到评测机环境的 Docker 镜像.

使用方法及其他详情请参考该仓库的 [README](https://github.com/pku-minic/oj-docker/blob/master/README.md).
