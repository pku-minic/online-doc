# Lv1.5. 测试

如果你已经完成了前四节的阅读, 你就可以顺利地得到一个最初级的编译器了, 接下来要做的事情是测试.

## 本地测试

!> 本地测试很重要! 请务必认真完成.
<br><br>
编译实践不同于其他同样使用 OJ 的课程: 你向 OJ 提交的并不是单个的代码文件, 而是一个完整的编译器项目. 如果不在本地的实验环境内预先测试/调试, 提交在线评测后, 你可能会遇到很多无从下手的问题.

假设你已经完成了 [Docker 的配置](/lv0-env-config/docker), 你可以执行:

```
docker run -it --rm -v 项目目录:/root/compiler maxxing/compiler-dev \
  autotest -koopa -s lv1 /root/compiler
```

你需要将 `项目目录` 替换为你的编译器项目在宿主机上的路径. 同时, 在运行测试前, 你需要确保你的编译器 (假设名称为 `compiler`) 能处理如下的命令行参数:

```
compiler -koopa 输入文件 -o 输出文件
```

其中, `-koopa` 代表你的编译器要输出 Koopa IR 文件, `输入文件` 代表输入的 SysY 源文件的路径, `输出文件` 代表 Koopa IR 的输出文件路径. 你的编译器应该解析 `输入文件`, 并把生成的 Koopa IR 输出到 `输出文件` 中.

测试程序会使用你的编译器将输入编译为 Koopa IR, 然后借助 LLVM 将 Koopa IR 进一步编译成可执行文件. 最后, 测试程序执行可执行文件, 检查程序的返回值 (也就是 `main` 的返回值) 是否符合预期. 测试程序**不会**检查你输出的 Koopa IR 的形式, 你输出的 IR **只要功能正确, 即可通过测试.**

关于实验环境/测试脚本的详细使用方法, 请参考[实验环境使用说明](/misc-app-ref/environment). 关于调试编译器的相关思路, 请参考[调试你的编译器](/misc-app-ref/environment?id=调试你的编译器). 关于测试脚本的工作原理, 请 [RTFSC](https://github.com/pku-minic/compiler-dev/blob/master/autotest/autotest).

## 上传代码到评测平台

学期初, 我们会向所有选修编译原理课的同学的 PKU 邮箱中发送在线评测平台的账号, 详情请关注课上的说明, 或课程群通知.

你可以使用发放的账号登录评测平台的代码托管平台 ([eduxiji.gitlab.net](https://gitlab.eduxiji.net)), 然后新建 repo. 之后你就可以按照使用 Git 的一般流程来向代码托管平台提交代码了.

!> **注意:** 请务必将你创建的 repo 的可见性设为 “Private”, 否则所有人都将在平台上看到你提交的代码!
<br><br>
此外, 平台的 GitLab **不支持 SSH 登录**, 在从平台 clone 仓库或向平台提交代码时, 请注意使用 HTTPS.

## 在线评测

?> **TODO:** 待补充.

关于在线评测系统的详细使用方法, 请参考[在线评测使用说明](/misc-app-ref/oj).
