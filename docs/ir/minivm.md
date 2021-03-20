# 4.3. 使用 MiniVM 调试

MiniVM 是专为编译原理课程实践设计的虚拟机 (HLLVM), 你可以使用它运行/调试符合 Eeyore/Tigger IR 格式的程序.

## 获取并编译 MiniVM

考虑到大家的开发环境各不相同, MiniVM 并未提供任何预编译的二进制文件. 首先请确认你的开发环境中具备:

* `cmake` 3.13+
* 支持 C++17 标准的 C++ 编译器
* `readline` 库

然后, 你可以从 GitHub 获取并编译 MiniVM:

```
$ git clone --recursive https://github.com/pku-minic/MiniVM.git
$ cd MiniVM
$ mkdir build
$ cd build
$ cmake .. && make -j8
```

编译完成的 MiniVM 会出现在 `build` 目录内:

```
$ pwd
/path/to/MiniVM/build
$ ./minivm -v
MiniVM Eeyore/Tigger Virtual Machine version 0.0.1

MiniVM is a virtual machine for interpreting Eeyore/Tigger IR,
which is designed for PKU compiler course.

Copyright (C) 2010-2020 MaxXing. License GPLv3.
```

需要注意的是, MiniVM 暂未在 Windows 和基于 M1 芯片的 macOS 平台上进行过任何测试, 但理论上在这些平台使用 MiniVM 时并不会出现太多问题. 如果你在上述平台中编译/使用 MiniVM 时遇到了问题, 欢迎向我们反馈, 我们会结合你的情况调整并更新 MiniVM, 十分感谢.

## 运行 Eeyore/Tigger 程序

假设你的编译器产生了这样一段 Eeyore 程序:

```eeyore
f_fib [1]
  var t0
  var t1

  if p0 > 2 goto l0
  return 1
l0:
  t0 = p0 - 1
  t1 = p0 - 2
  param t0
  t0 = call f_fib
  param t1
  t1 = call f_fib
  t0 = t0 + t1
  return t0
end f_fib

f_main [0]
  var t0

  t0 = call f_getint
  param t0
  t0 = call f_fib
  param t0
  call f_putint
  param 10
  call f_putch
  return 0
end f_main
```

这个程序会从 `stdin` 读取一个整数 `n`, 然后计算斐波那契数列的第 `n` 项.

你可以将其存储在文件 `fib.eeyore` 中, 然后使用 MiniVM 执行:

```
$ ./minivm fib.eeyore
10
55
```

可见, 程序的输出是正确的.

同理, 假设你的编译器输出了一份对应的 Tigger 程序, 并将其存储在了文件 `fib.tigger` 中, 则你可以执行:

```
$ ./minivm -t fib.eeyore
```

来运行这个程序. `-t` 参数会告诉 MiniVM 当前执行的程序是一个 Tigger 程序. MiniVM 支持如下命令行参数:

```
$ ./minivm -h
Usage: minivm <INPUT> [OPTIONS...]

Arguments:
  input                        input Eeyore/Tigger IR file

Options:
  -h, --help                   show this message
  -v, --version                show version info
  -t, --tigger                 run in Tigger mode
  -d, --debug                  enable debugger
  -o, --output <ARG>           output file, default to stdout
  -dg, --dump-gopher           dump Gopher to output
  -db, --dump-bytecode         dump bytecode to output
```

## 调试 Eeyore/Tigger 程序

> 施工中...

## 进阶话题: MiniVM 的原理

> 这部分内容并不在编译课程实践的要求之内, 如果你对此不感兴趣, 可跳过这一节.

> 施工中...
