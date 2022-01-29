# 北大编译实践在线文档

欢迎各位同学选择编译原理课程实践!

在本课程中, 你将实现一个可将 SysY 语言编译到 RISC-V 汇编的编译器. SysY 语言是一种精简版的 C 语言, RISC-V 则是一种新兴且热门的指令系统 (ISA). 而你的编译器, 则需要在这两者之间建立联系.

通常情况下, SysY 程序看起来和 C 程序类似:

```c
int fib(int n) {
  if (n <= 2) {
    return 1;
  } else {
    return fib(n - 1) + fib(n - 2);
  }
}

int main() {
  int input = getint();
  putint(fib(input));
  putch(10);
  return 0;
}
```

上述程序可以被编译成如下的 RISC-V 汇编 (仅作示例, 实际编译得到的汇编取决于编译器的具体实现):

```asm
  .text
  .align  2

  .globl fib
fib:
  sw    ra, -4(sp)
  addi  sp, sp, -16
  li    t1, 2
  bgt   a0, t1, .l0
  li    a0, 1
  addi  sp, sp, 16
  lw    ra, -4(sp)
  ret
.l0:
  addi  s4, a0, -1
  sw    a0, 0(sp)
  mv    a0, s4
  call  fib
  mv    a3, a0
  lw    a0, 0(sp)
  addi  s4, a0, -2
  sw    a3, 0(sp)
  mv    a0, s4
  call  fib
  mv    s4, a0
  lw    a3, 0(sp)
  add   s4, a3, s4
  mv    a0, s4
  addi  sp, sp, 16
  lw    ra, -4(sp)
  ret

  .globl main
main:
  sw    ra, -4(sp)
  addi  sp, sp, -16
  call  getint
  call  fib
  call  putint
  li    a0, 10
  call  putch
  li    a0, 0
  addi  sp, sp, 16
  lw    ra, -4(sp)
  ret
```

以上的这些新名词你可能并不熟悉, 编译器的工作原理你也许更是知之甚少. 但相信上完这门课程, 你将对这些内容, 乃至计算机系统底层的工作原理, 拥有一个崭新的认识.

[让我们开始吧! Link start!](/preface/)
