# Lv9.4. 测试

“咔哒!”

你按下了 `Ctrl + S` (也可能是 `Cmd + S`), 动作干净利落, 仿佛武士收刀入鞘. 眼前那条曾在你眼中永远都无法击败的喷火龙, 现在已经奄奄一息.

脚踏一片焦土, 眼前是黎明的曙光, 心中则是百感交集.

至此, 你的编译器已经可以处理所有合法的 SysY 程序了! 祝贺, 你是最棒的!

在完成本章之前, 先进行一些测试吧.

## 本地测试

### 只测试本章

测试 Koopa IR:

```
docker run -it --rm -v 项目目录:/root/compiler maxxing/compiler-dev \
  autotest -koopa -s lv9 /root/compiler
```

测试 RISC-V 汇编:

```
docker run -it --rm -v 项目目录:/root/compiler maxxing/compiler-dev \
  autotest -riscv -s lv9 /root/compiler
```

### 测试所有章节

测试 Koopa IR:

```
docker run -it --rm -v 项目目录:/root/compiler maxxing/compiler-dev \
  autotest -koopa /root/compiler
```

测试 RISC-V 汇编:

```
docker run -it --rm -v 项目目录:/root/compiler maxxing/compiler-dev \
  autotest -riscv /root/compiler
```

## 在线评测

?> **TODO:** 待补充.
