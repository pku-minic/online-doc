# Lv3.4. 测试

目前你的编译器已经可以处理一些简单的表达式计算了, 就像计算器一样, 可喜可贺!

在完成本章之前, 先进行一些测试吧.

## 本地测试

测试 Koopa IR:

```
docker run -it --rm -v 项目目录:/root/compiler compiler-dev \
  autotest -koopa -s lv3 /root/compiler
```

测试 RISC-V 汇编:

```
docker run -it --rm -v 项目目录:/root/compiler compiler-dev \
  autotest -riscv -s lv3 /root/compiler
```

测试程序对编译器的要求和之前章节一致, 此处及之后章节将不再赘述.

## 在线评测

?> **TODO:** 待补充.
