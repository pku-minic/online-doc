# Lv2. 初试目标代码生成

本章中, 你将在上一章的基础上, 实现一个能处理 `main` 函数和 `return` 语句的编译器, 同时输出编译后的 RISC-V 汇编.

你的编译器会将如下的 SysY 程序:

```c
int main() {
  // 摊牌了, 我是注释
  return 0;
}
```

编译为对应的 RISC-V 汇编:

```
  .text
  .globl main
main:
  li a0, 0
  ret
```

或:

```
  .text
  .globl main
main:
  li t0, 0
  mv a0, t0
  ret
```

取决于你的实现方式.

## 相关规范

见 [Lv1. `main` 函数](/lv1-main/).
