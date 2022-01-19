# Lv0.3. RISC-V 简介

?> 本节将带你大致认识 RISC-V 指令系统, 后续章节中将结合实践内容, 详细介绍 RISC-V 指令系统中对应部分的特性.
<br><br>
关于 RISC-V 的更多介绍, 请参考 [RISC-V 官网](https://riscv.org/). 关于 RISC-V 中指令的相关定义, 请参考 [RISC-V 指令速查](/misc-app-ref/riscv-insts).

## 什么是 RISC-V

在编译实践中, 你将开发一个生成 RISC-V 汇编的编译器. 那么首先, 什么是 RISC-V?

RISC-V 是由加州大学伯克利分校设计并推广的第五代 RISC 指令系统体系结构 (ISA). RISC-V 没有任何历史包袱, 设计简洁, 高效低能耗, 且高度模块化——最主要的, 它还是一款完全开源的 ISA.

RISC-V 的指令系统由基础指令系统 (base instruction set) 和指令系统扩展 (extension) 构成. 每个 RISC-V 处理器必须实现基础指令系统, 同时可以支持若干扩展. 常用的基础指令系统有两种:

* `RV32I`: 32 位整数指令系统.
* `RV64I`: 64 位整数指令系统. 兼容 `RV32I`.

常用的标准指令系统扩展包括:

* `M` 扩展: 包括乘法和除法相关的指令.
* `A` 扩展: 包括原子内存操作相关的指令.
* `F` 扩展: 包括单精度浮点操作相关的指令.
* `D` 扩展: 包括双精度浮点操作相关的指令.
* `C` 扩展: 包括常用指令的 16 位宽度的压缩版本.

我们通常使用 `RV32/64I` + 扩展名称的方式来描述某个处理器/平台支持的 RISC-V 指令系统类型, 例如 `RV32IMA` 代表这个处理器是一个 32 位的, 支持 `M` 和 `A` 扩展的 RISC-V 处理器.

在课程实践中, 你的编译器将生成 `RV32IM` 范围内的 RISC-V 汇编.

一个使用 RISC-V 汇编编写的程序如下:

```asm
  # 代码段.
  .text
  # `main` 函数, 程序的入口.
  .globl main
main:
  addi  sp, sp, -12
  sw    ra, 8(sp)
  sw    s0, 4(sp)
  sw    s1, 0(sp)
  la    s0, hello_str
  li    s1, 0
1:
  add   a0, s0, s1
  lbu   a0, 0(a0)
  beqz  a0, 1f
  call  putch
  addi  s1, s1, 1
  j     1b
1:
  li    a0, 0
  lw    s0, 4(sp)
  lw    s1, 0(sp)
  lw    ra, 8(sp)
  addi  sp, sp, 12
  ret

  # 数据段.
  .data
  # 字符串 "Hello, world!\n\0".
hello_str:
  .asciz "Hello, world!\n"
```

## 编译/运行 RISC-V 程序

假设你已经把一个 RISC-V 汇编程序保存在了文件 `hello.S` 中, 你可以在实验环境中将这个 RISC-V 程序汇编并链接成可执行文件, 然后运行这个可执行文件:

```
clang hello.S -c -o hello.o -target riscv32-unknown-linux-elf -march=rv32im -mabi=ilp32
ld.lld hello.o -L$CDE_LIBRARY_PATH/riscv32 -lsysy -o hello
qemu-riscv32-static hello
```
