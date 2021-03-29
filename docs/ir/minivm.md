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

需要注意的是, MiniVM 暂未在基于 M1 芯片的 macOS 平台 (以及其他非 `x86-64` 架构平台) 上进行过任何测试, 但理论上在这些平台使用 MiniVM 时并不会出现太多问题. 如果你在上述平台中编译/使用 MiniVM 时遇到了问题, 欢迎向我们反馈, 我们会结合你的情况调整并更新 MiniVM, 十分感谢.

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
$ ./minivm -t fib.tigger
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

依然以[上一小节](ir/minivm?id=运行-eeyoretigger-程序)的 Eeyore 程序为例, 如果我们想调试这个程序, 可以在命令行参数中添加 `-d` 选项:

```
$ ./minivm fib.eeyore -d
```

此时, MiniVM 附带的调试器 MiniDbg 会开始运行. MiniDbg 的基本使用方法和 GDB 类似, 你可以使用 `help` 命令查看其支持的所有命令:

```
minidbg> help
Debugger commands:
      break/b    [POS] --- set breakpoint at POS
   continue/c          --- continue running
     delete/d      [N] --- delete breakpoint/watchpoint
    disasm/da  [N POS] --- Show source code, or disassemble VM instructions
         help    [CMD] --- show help message of CMD
         info     ITEM --- show information of ITEM
       layout      FMT --- set layout of disassembler
       next/n          --- stepping over calls (source level)
     nexti/ni      [N] --- stepping over calls (instruction level)
      print/p   [EXPR] --- show value of EXPR
       quit/q          --- quit debugger
       step/s          --- stepping into calls (source level)
     stepi/si      [N] --- stepping into calls (instruction level)
      watch/w     EXPR --- set watchpoint at EXPR
            x   N EXPR --- examine memory at EXPR
```

在上述帮助信息中包含了一些记法:

* `POS`: 位置信息, 可以是:
    * Eeyore/Tigger 源代码的行数, 形如 `:123`
    * MiniVM 程序计数器 (`pc`) 的值, 形如 `123`
    * Eeyore/Tigger 程序中的函数或标号, 形如: `f_func` 或 `l0`.
* `EXPR`: 包含四则运算, 逻辑运算, 位运算, 比较运算的二元或一元表达式, 表达式中可以包含:
    * 整数常量, 形如 `1`, `12450`
    * Eeyore/Tigger 中的变量, 形如 `T0`, `t1`, `p2`
    * 寄存器标号, 形如 `$s0`, `$a0`, `$pc`
    * 对某个内存地址的访问, 形如 `*T0`, `*(T0 + 12)` 或其他更复杂的带 `*` 的表达式.

如果你想知道某条指令 `CMD` 的具体信息, 则可以使用 `help CMD` 命令, 比如执行 `help info`:

```
minidbg> help info
Syntax: info ITEM
  Show information of ITEM.

ITEM:
  stack/s  --- operand stack
  env/e    --- environment stack
  reg/r    --- static registers
  break/b  --- breakpoints
  watch/w  --- watchpoints
```

举个例子, 如果你想让 MiniVM 在执行函数 `f_fib` 时停下, 那么你可以执行:

```
minidbg> b f_fib
```

此时 `f_fib` 处就会被添加一个断点, 你可以使用 `info b` 查看其详细信息:

```
minidbg> info b
number of breakpoints: 1
  breakpoint #0: pc = 1, hit_count = 0
```

执行 `continue` 命令 (或者缩写为 `c` 命令), MiniVM 将继续运行, 直到遇到断点/监视点, 或者用户按下了 `^C`:

```
minidbg> c
```

这个时候程序会卡住. 为什么会卡住呢? 因为这个 Eeyore 程序会调用 `f_getint` 从 `stdin` 读取一个整数, 将其作为参数传入到 `f_fib` 中. 所以我们只需要随便输出一个整数, 然后按回车, MiniVM 就会继续执行, 并瞬间在 `f_fib` 函数的断点处停下:

```
minidbg> c
10
breakpoint hit, pc = 1, at line 2

 B>    2:    var t0
       3:    var t1
       4:  
       5:    if p0 > 2 goto l0
       6:    return 1
       7:  l0:
       8:    t0 = p0 - 1
       9:    t1 = p0 - 2
      10:    param t0
      11:    t0 = call f_fib
```

此时你可以根据你的需要执行进一步的操作, 比如单步执行程序:

```
minidbg> n

   3:    var t1
   4:  
   5:    if p0 > 2 goto l0
   6:    return 1
   7:  l0:
   8:    t0 = p0 - 1
   9:    t1 = p0 - 2
  10:    param t0
  11:    t0 = call f_fib
  12:    param t1
```

你可以尝试一直单步执行 (step over), 直到程序结束, 并在这个过程中使用其他命令观察 MiniVM 内部状态的变化. 当然, 在这个过程中, 你可能会多次遇到 `f_fib` 处的断点, 你也许需要将它删除. 具体操作请自行参考 `help` 命令.

在编译实践课程中, 你可能会多次用到 MiniVM 和 MiniDbg, 所以我们建议你熟悉命令行界面的调试器的基本使用方式, 比如:

* step into 和 step over 有何区别?
* 如何在合适的位置添加断点?
* 如何在合适的时刻删除断点?
* 如何使用监视点 (watchpoint) 功能监视变量/寄存器的值的变化, 甚至用它替代断点?
* 其他更为进阶的话题.

MiniDbg 虽然远不如 GDB 强大, 但它提供的诸多基本功能已经足以组合出许多令人意想不到的用法了. 相信有了 MiniDbg, 你就能在你的编译器生成的 Eeyore/Tigger 程序出问题时, 更快地发现问题的所在.

## 进阶话题: MiniVM 的原理

> 这部分内容并不在编译课程实践的要求之内, 如果你对此不感兴趣, 可跳过这一节.

> 施工中...
