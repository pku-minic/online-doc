# Lv8.4. 测试

到目前为止, 你的编译器已经可以处理包括函数定义和调用, SysY 库函数和全局变量的程序了, 这又是一次巨大的飞跃!

有了 SysY 库函数, 你的编译器生成的程序就能进行输入/输出字符之类的 I/O 操作了. 测试程序会通过指定标准输入以及检查标准输出的方式, 来进一步确认你的程序是否执行正确.

已经可以看到胜利的曙光了, 加油!

在完成本章之前, 先进行一些测试吧.

## 本地测试

测试 Koopa IR:

```
docker run -it --rm -v 项目目录:/root/compiler compiler-dev \
  autotest -koopa -s lv8 /root/compiler
```

测试 RISC-V 汇编:

```
docker run -it --rm -v 项目目录:/root/compiler compiler-dev \
  autotest -riscv -s lv8 /root/compiler
```

## 在线评测

?> **TODO:** 待补充.
