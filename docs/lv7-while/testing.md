# Lv7.3. 测试

到目前为止, 你的编译器已经可以处理分支和循环这两种复杂的程序结构了, 越来越像那么回事了!

在完成本章之前, 先进行一些测试吧.

## 本地测试

测试 Koopa IR:

```
docker run -it --rm -v 项目目录:/root/compiler compiler-dev \
  autotest -koopa -s lv7 /root/compiler
```

测试 RISC-V 汇编:

```
docker run -it --rm -v 项目目录:/root/compiler compiler-dev \
  autotest -riscv -s lv7 /root/compiler
```

## 在线评测

?> **TODO:** 待补充.
