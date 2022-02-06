# Lv8.2. SysY 库函数

本节没有任何语法规范上的变化.

## 一个例子

```c
int main() {
  return getint();
}
```

## 词法/语法分析

因为语法规范不变, 所以这部分没有需要改动的内容.

## 语义分析

根据 SysY 的规定, SysY 库函数可以不加声明就直接使用, 所以你可能需要预先在全局符号表中添加和库函数相关的符号定义, 以防无法正确处理相关内容.

参考 [SysY 运行时库](/misc-app-ref/sysy-runtime).

## IR 生成

虽然 SysY 中可以不加声明就使用所有库函数, 但在 Koopa IR 中, 所有被 `call` 指令引用的函数必须提前声明, 否则会出现错误. 你可以使用 `decl` 语句来预先声明所有的库函数.

示例程序生成的 Koopa IR 为:

```koopa
decl @getint(): i32
decl @getch(): i32
decl @getarray(*i32): i32
decl @putint(i32)
decl @putch(i32)
decl @putarray(i32, *i32)
decl @starttime()
decl @stoptime()

fun @main(): i32 {
%entry:
  %0 = call @getint()
  ret %0
}
```

?> 注: `decl` 要求在括号内写明参数的类型, 某些库函数会接收数组参数, 你可以认为这种参数的类型是 `*i32`, 即 `i32` 的指针. Lv9 将讲解其中的具体原因.

## 目标代码生成

RISC-V 汇编中, 函数符号无需声明即可直接使用. 关于到底去哪里找这些外部符号, 这件事情由链接器负责. 除此之外, 调用库函数和调用 SysY 内定义的函数并无区别.

Koopa IR 中, 函数声明是一种特殊的函数, 它们和函数定义是放在一起的. 也就是说, 在上一节的基础上, 你需要在扫描函数时跳过 Koopa IR 中的所有函数声明.

Koopa IR 的函数声明和普通函数的区别是: 函数声明的基本块列表是空的. 在 C/C++ 中, 你可以通过判断 `koopa_raw_function_t` 中 `bbs` 字段对应的 slice 的长度, 来判断函数的基本块列表是否为空. 在 Rust 中, `FunctionData` 提供的 `layout()` 方法会返回函数内基本块/指令的布局, 返回类型为 `&Layout`. 而 `Layout` 中的 `entry_bb()` 方法可以返回函数入口基本块的 ID, 如果函数为声明, 这个方法会返回 `None`.

示例程序生成的 RISC-V 汇编为:

```
  .text
  .globl main
main:
  addi sp, sp, -16
  sw ra, 12(sp)
  call getint
  sw a0, 0(sp)
  lw a0, 0(sp)
  lw ra, 12(sp)
  addi sp, sp, 16
  ret
```
