# Lv5.2. 测试

目前你的编译器已经可以处理块语句了. 同时, 你的编译器在语义分析阶段还可以处理作用域. 非常棒!

在完成本章之前, 先进行一些测试吧.

## 本地测试

测试 Koopa IR:

```
docker run -it --rm -v 项目目录:/root/compiler maxxing/compiler-dev \
  autotest -koopa -s lv5 /root/compiler
```

测试 RISC-V 汇编:

```
docker run -it --rm -v 项目目录:/root/compiler maxxing/compiler-dev \
  autotest -riscv -s lv5 /root/compiler
```

## 在线评测

?> **TODO:** 待补充.
