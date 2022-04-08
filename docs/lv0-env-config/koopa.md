# Lv0.2. Koopa IR 简介

?> 本节将带你大致了解什么是 Koopa IR, 后续章节中将结合实践内容, 详细介绍 Koopa IR 对应部分的特性.
<br><br>
关于 Koopa IR 的具体定义, 请参考 [Koopa IR 规范](/misc-app-ref/koopa).

## 什么是 Koopa IR

Koopa IR 是一种专为北京大学编译原理课程实践设计的教学用的中间表示 (IR), 它在设计上类似 LLVM IR, 但简化了很多内容, 方便大家上手和理解.

同时, 我们为 Koopa IR 开发了对应的框架 ([koopa](https://github.com/pku-minic/koopa) 和 [libkoopa](https://github.com/pku-minic/koopa/tree/master/crates/libkoopa)), 大家在使用 C/C++/Rust 编程时, 可以直接调用框架的接口, 实现 Koopa IR 的生成/解析/转换.

Koopa IR 是一种强类型的 IR, IR 中的所有值 (`Value`) 和函数 (`Function`) 都具备类型 (`Type`). 这种设计避免了一些 IR 定义上的模糊之处, 例如之前的教学用 IR 完全不区分整数变量和数组变量, 很容易出现混淆; 同时可以在生成 IR 之前就确定 IR 中存在的部分问题, 例如将任意整数作为内存地址并向其中存储数据.

Koopa IR 中, 基本块 (basic block) 必须是显式定义的. 即, 在描述函数内的指令时, 你必须把指令按照基本块分组, 每个基本块结尾的指令只能是分支/跳转/函数返回指令之一. 在 IR 的数据结构表示上, 指令也会被按照基本块分类. 这很大程度上方便了 IR 的优化, 因为许多优化算法都是在基本块的基础上对程序进行分析/变换的.

Koopa IR 还是一种 SSA 形式的 IR. 虽然这部分内容在课程实践中并非必须掌握, 但考虑到有些同学可能希望在课程实践的要求上, 做出一个更完备, 更强大的编译器, 我们将 Koopa IR 设计成了同时兼容非 SSA 形式和 SSA 形式的样子. 基于 SSA 形式下的 Koopa IR, 你可以开展更多复杂且有效的编译优化.

一个用 Koopa IR 编写的 “Hello, world!” 程序如下:

```koopa
// SysY 中的 `putch` 函数的声明.
decl @putch(i32)

// 一个用来输出字符串 (其实是整数数组) 的函数.
// 函数会扫描输入的数组, 将数组中的整数视作 ASCII 码, 并作为字符输出到屏幕上,
// 遇到 0 时停止扫描.
fun @putstr(@arr: *i32) {
%entry:
  jump %loop_entry(@arr)

// Koopa IR 采用基本块参数代替 SSA 形式中的 Phi 函数.
// 当然这部分内容并不在实践要求的必选内容之中, 你无需过分关注.
%loop_entry(%ptr: *i32):
  %cur = load %ptr
  br %cur, %loop_body, %end

%loop_body:
  call @putch(%cur)
  %next = getptr %ptr, 1
  jump %loop_entry(%next)

%end:
  ret
}

// 字符串 "Hello, world!\n\0".
global @str = alloc [i32, 15], {
  72, 101, 108, 108, 111, 44, 32, 119, 111, 114, 108, 100, 33, 10, 0
}

// `main` 函数, 程序的入口.
fun @main(): i32 {
%entry:
  %str = getelemptr @str, 0
  call @putstr(%str)
  ret 0
}
```

?> **注意:** 上述代码只是一个示例, **你暂时不需要理解它的含义.** 在之后的章节中, 我们会逐步介绍 Koopa IR 的相关内容.

## 在线体验 Koopa IR

?> **TODO:** 待补充

## 本地运行 Koopa IR

假设你已经把一个 Koopa IR 程序保存在了文件 `hello.koopa` 中, 你可以在实验环境中运行这个 Koopa IR 程序:

```
koopac hello.koopa | llc --filetype=obj -o hello.o
clang hello.o -L$CDE_LIBRARY_PATH/native -lsysy -o hello
./hello
```
