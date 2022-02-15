# Lv4.3. 测试

本章的涉及的内容相对较多, 理解难度相较前几章也更难. 你能进行到这一步实属不易, 给你比一个~大母猪~大拇指! ( ´∀`)b

目前你的编译器已经可以处理常量和变量了, 能处理的程序看起来也已经有模有样了, 十分不错!

在完成本章之前, 先进行一些测试吧.

## 本地测试

测试 Koopa IR:

```
docker run -it --rm -v 项目目录:/root/compiler compiler-dev \
  autotest -koopa -s lv4 /root/compiler
```

测试 RISC-V 汇编:

```
docker run -it --rm -v 项目目录:/root/compiler compiler-dev \
  autotest -riscv -s lv4 /root/compiler
```

## 在线评测

?> **TODO:** 待补充.
