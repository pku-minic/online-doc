# Lv6.3. 测试

你的编译器已经可以处理 `if/else` 语句了, 它能处理的程序又变得复杂了很多, 看起来也不再像个简单的计算器了, 事情变得有趣了起来!

在完成本章之前, 先进行一些测试吧.

## 本地测试

测试 Koopa IR:

```
docker run -it --rm -v 项目目录:/root/compiler compiler-dev \
  autotest -koopa -s lv6 /root/compiler
```

测试 RISC-V 汇编:

```
docker run -it --rm -v 项目目录:/root/compiler compiler-dev \
  autotest -riscv -s lv6 /root/compiler
```

## 在线评测

?> **TODO:** 待补充.
