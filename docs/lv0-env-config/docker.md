# Lv0.1. 配置 Docker

Docker 是容器技术的一种实现, 而容器技术又是一种轻量级的虚拟化技术. 你可以简单地把容器理解成虚拟机: 容器中可以运行另一个操作系统, 它和你的宿主系统是隔离的.

当然, 容器和虚拟机实际上并不相同, 你若感兴趣可自行 STFW, 此处不做过多介绍.

基于 Docker, 我们可以很方便地完成各类 “配环境” 的操作:

* 负责配置环境的人只需要写好 `Dockerfile`, 然后使用 Docker 构建镜像即可. 和环境相关的所有内容, 包括系统里的某些配置, 或者安装的工具链, 都被封装在了镜像里.
* 需要使用环境的人只要拿到镜像, 就可以基于此创建一个容器, 然后在里面完成自己的工作. 开箱即用, 不需要任何多余的操作, 十分省时省力.
* 如果某天不再需要环境, 直接把容器和镜像删除就完事了, 没残留也不拖泥带水, 干净又卫生.

## 安装 Docker

你可以访问 [Docker 的官方网站](https://docs.docker.com/get-docker/) 来安装 Docker. 安装完毕后, 你可能需要重启你的系统.

鉴于许多其他课程都要求使用 Linux 操作系统完成各类操作, 而很多同学的电脑都安装了 Windows 系统, 所以大家的电脑中可能都配置了装有 Linux 系统的虚拟机. 考虑到这种情况, 此处需要说明: Docker 是支持 Windows, macOS 和 Linux 三大平台的, 所以**你可以直接在你的宿主系统 (而不是虚拟机中) 安装 Docker**.

安装完毕后, 打开系统的命令行:

* 如果你使用的是 macOS 或 Linux, 你可以使用系统的默认终端.
* 如果你使用的是 Windows, 你可以打开 PowerShell.

执行:

```
docker
```

你将会看到 Docker 的帮助信息.

## 获取编译实践的镜像

在系统的命令行中执行:

```
docker pull maxxing/compiler-dev
```

如果你使用的是 Linux 系统, 则上述命令可能需要 `sudo` 才可正常执行.

编译实践的镜像较大, 但拉取镜像的速度可能并不快. 为了加快从 Docker Hub 拉取镜像的速度, 你可以自行 STFW, 为你系统中的 Docker 配置 Docker Hub Mirror.

## Docker 的基本用法

你可以使用如下命令在编译实践的 Docker 镜像中执行命令:

```
docker run maxxing/compiler-dev ls -l /
```

你会看到屏幕上出现了 `ls -l /` 命令的输出, 内容是 `compiler-dev` 镜像根目录里所有文件的列表.

这个命令实际上会完成以下几件事:

* 使用 `compiler-dev` 这个镜像创建一个临时的容器.
* 启动这个临时容器.
* 在这个临时容器中执行命令 `ls -l /`.
* 关闭容器.

这里其实出现了两个概念: “镜像” 和 “容器”. 你可以把它们理解为: 前者是一个硬盘, 里面装好了操作系统, 但它是静态的, 你不能直接拿它来运行. 后者是一台电脑, 里面安装了硬盘, 就能运行对应的操作系统.

当然实际上, 你可以在容器里修改文件系统的内容, 比如创建或者删除文件, 而容器对应的镜像完全不受影响. 比如你在容器里删文件把系统搞挂了, 这时候你只需要删掉这个容器, 然后从镜像创建一个新的容器, 一切就会还原到最初的样子.

刚刚的命令会根据 `compiler-dev` 创建一个容器, 但 Docker 并不会删除这个容器. 我们可以查看目前 Docker 中所有的容器:

```
$ docker ps -a
CONTAINER ID  IMAGE                        COMMAND     CREATED         STATUS                     PORTS       NAMES
696cbe1128ca  maxxing/compiler-dev:latest  ls -l /     19 seconds ago  Exited (0) 19 seconds ago              vibrant_tharp
```

命令会列出刚刚我们执行 `docker run` 时创建的临时容器. 很多情况下, 我们只是想用镜像里的环境做一些一次性的工作, 比如用里面的测试脚本测试自己的编译器, 然后查看测试结果. 在此之后这个临时容器就没有任何作用了. 我们可以执行如下命令来删除这个容器:

```
docker rm 696cbe1128ca
```

其中, `696cbe1128ca` 是 `docker ps -a` 命令输出的容器 ID.

当然我们可以简化上述操作:

```
docker run --rm maxxing/compiler-dev ls -l /
```

这条命令会使用 `compiler-dev` 镜像创建一个临时容器, 并在其中运行 `ls -l /` 命令, 然后删除刚刚创建的临时容器. 再次执行 `docker ps -a`, 你可以看到, 刚刚创建的容器并没有留下来.

我们还可以使用另一种方式运行容器:

```
docker run -it --rm maxxing/compiler-dev bash
```

这条命令会使用 `compiler-dev` 创建容器, 并在其中执行 `bash`——这是许多 Linux 发行版的默认 Shell, 也就是大家启动终端后看到的命令行界面. 为了能在 Shell 中操作, 我们使用了 `-it` 参数, 这个参数会开启容器的 `stdin` 以便我们输入 (`-i`), 同时 Docker 会为容器分配一个终端 (`-t`).

执行完这条命令之后, 你会发现你进入了容器的 Shell, 你可以在其中执行任何命令:

```
root@e677c2d348fe:~# ls /
bin  boot  dev  etc  home  lib  lib32  lib64  libx32  media  mnt  opt  proc  root  run  sbin  srv  sys  tmp  usr  var
```

如需退出, 你可以执行 `exit`, 或者按下 `Ctrl + D`. 因为我们添加了 `--rm` 选项, Docker 会在退出后删除刚刚的容器, 所以在这种情况下请一定不要在容器里保存重要的内容.

在许多情况下, 我们需要让 Docker 容器访问宿主系统中的文件. 比如你的编译器存放在宿主机的 `/home/max/compiler` 目录下, 你希望 Docker 容器也能访问到这个目录里的内容, 这样你就可以使用容器中的测试脚本测试你的编译器了. 你可以执行:

```
docker run -it --rm -v /home/max/compiler:/root/compiler maxxing/compiler-dev bash
```

这条命令和之前的命令相比多了一个 `-v /home/max/compiler:/root/compiler` 选项, 这个选项代表: 我希望把宿主机的 `/home/max/compiler` 目录, 挂载 (mount) 到容器的 `/root/compiler` 目录. 这样, 在进入容器之后, 我们就可以通过访问 `/root/compiler` 来访问宿主机的 `/home/max/compiler` 目录了.

关于 Docker 的其他用法, 请参考 [Docker 的官方文档](https://docs.docker.com/engine/reference/commandline/docker/), 或根据情况自行 STFW.

## 免责声明

!> 请务必注意如下内容!

MaxXing 在设计 `compiler-dev` 的镜像时, 只考虑了直接使用 `docker run` 命令启动容器并在其中运行程序的操作, 并且**只对这种情况进行了测试**.

如果你使用其他方式连接了 Docker 容器, 例如在容器内安装了一个 SSH 然后远程连接, 则我们**不保证**这种使用方式不会出问题!

为避免遇到更多的问题, 我们建议你按照文档的指示来使用 Docker.
